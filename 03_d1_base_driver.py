#!/usr/bin/env python3
import math
import struct
import serial

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
from tf2_ros import TransformBroadcaster


class D1BaseDriver(Node):
    def __init__(self):
        super().__init__("d1_base_driver")

        # Configurable ROS 2 parameters (override via CLI: --ros-args -p port:=/dev/ttyUSB0 -p dry_run:=false)
        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("wheel_separation", 0.44)   # D1 footprint is 0.58 m wide -> track ~0.44 m
        self.declare_parameter("wheel_radius", 0.085)      # Measure actual wheel radius in meters
        self.declare_parameter("max_linear_vel", 0.5)      # House rule: walking pace limit (m/s)
        self.declare_parameter("max_angular_vel", 1.0)     # Max yaw rate (rad/s)
        self.declare_parameter("watchdog_timeout", 0.2)    # 200 ms deadman watchdog timeout
        self.declare_parameter("dry_run", True)            # True allows testing without serial hardware

        self.port_name = self.get_parameter("port").value
        self.baudrate = self.get_parameter("baudrate").value
        self.wheel_sep = self.get_parameter("wheel_separation").value
        self.wheel_rad = self.get_parameter("wheel_radius").value
        self.max_lin = self.get_parameter("max_linear_vel").value
        self.max_ang = self.get_parameter("max_angular_vel").value
        self.watchdog_timeout = self.get_parameter("watchdog_timeout").value
        self.dry_run = self.get_parameter("dry_run").value

        # Command and safety state
        self.target_v = 0.0
        self.target_w = 0.0
        self.estop_active = False
        self.last_cmd_time = self.get_clock().now()

        # Odometry integration state
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_odom_time = self.get_clock().now()

        # Open serial connection to motor controller
        self.ser = None
        if not self.dry_run:
            self.ser = serial.Serial(self.port_name, baudrate=self.baudrate, timeout=0.01)
            self.get_logger().info(f"Opened serial port: {self.port_name} @ {self.baudrate}")
        else:
            self.get_logger().warn("DRY_RUN enabled — motor commands will not be sent over serial.")

        # ROS 2 publishers, subscribers, and TF broadcaster
        self.cmd_sub = self.create_subscription(Twist, "/cmd_vel", self.cmd_vel_callback, 10)
        self.estop_sub = self.create_subscription(Bool, "/estop", self.estop_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # 50 Hz (20 ms) control and safety watchdog loop
        self.control_timer = self.create_timer(0.02, self.control_loop)

    def estop_callback(self, msg: Bool):
        """Immediately halt motors when software E-Stop is triggered."""
        self.estop_active = msg.data
        if self.estop_active:
            self.target_v = 0.0
            self.target_w = 0.0
            self.send_wheel_velocities(0.0, 0.0)
            self.get_logger().error("E-STOP ENGAGED! Motors halted.")
        else:
            self.get_logger().info("E-STOP released.")

    def cmd_vel_callback(self, msg: Twist):
        """Clamp incoming velocity commands to safe walking-pace limits."""
        if self.estop_active:
            return
        self.target_v = max(-self.max_lin, min(self.max_lin, msg.linear.x))
        self.target_w = max(-self.max_ang, min(self.max_ang, msg.angular.z))
        self.last_cmd_time = self.get_clock().now()

    def control_loop(self):
        now = self.get_clock().now()
        dt_cmd = (now - self.last_cmd_time).nanoseconds / 1e9

        # Enforce 200 ms deadman watchdog: zero velocity if /cmd_vel stream stops
        if self.estop_active or dt_cmd > self.watchdog_timeout:
            v = 0.0
            w = 0.0
        else:
            v = self.target_v
            w = self.target_w

        # Differential-drive inverse kinematics (left/right wheel linear velocities in m/s)
        v_left = v - (w * self.wheel_sep / 2.0)
        v_right = v + (w * self.wheel_sep / 2.0)
        self.send_wheel_velocities(v_left, v_right)

        # Read feedback and broadcast odometry + TF
        dt_odom = (now - self.last_odom_time).nanoseconds / 1e9
        self.last_odom_time = now
        meas_v, meas_w = self.read_telemetry(v, w)
        self.publish_odometry(now, dt_odom, meas_v, meas_w)

    def send_wheel_velocities(self, v_left: float, v_right: float):
        """
        TODO: Replace packet structure with the reverse-engineered D1 motor protocol.
        Example frame: 0xAA 0x55 header + left/right int16 (mm/s) + XOR checksum.
        """
        left_mms = int(v_left * 1000.0)
        right_mms = int(v_right * 1000.0)
        payload = struct.pack("<BBhh", 0xAA, 0x55, left_mms, right_mms)
        checksum = 0
        for b in payload:
            checksum ^= b
        packet = payload + struct.pack("<B", checksum)

        if self.ser and self.ser.is_open:
            self.ser.write(packet)

    def read_telemetry(self, fallback_v: float, fallback_w: float):
        """
        TODO: Parse incoming encoder ticks or wheel velocities from the MCU serial stream.
        Falls back to commanded velocity until encoder decoding is plugged in.
        """
        if self.ser and self.ser.in_waiting > 0:
            _raw = self.ser.read(self.ser.in_waiting)
            # Decode left/right encoder counts here and compute actual (v, w)
        return fallback_v, fallback_w

    def publish_odometry(self, now, dt: float, v: float, w: float):
        """Integrate planar pose and publish both /odom and odom -> base_footprint TF."""
        self.x += v * math.cos(self.yaw) * dt
        self.y += v * math.sin(self.yaw) * dt
        self.yaw += w * dt

        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)
        stamp = now.to_msg()

        # Broadcast TF transform
        tf_msg = TransformStamped()
        tf_msg.header.stamp = stamp
        tf_msg.header.frame_id = "odom"
        tf_msg.child_frame_id = "base_footprint"
        tf_msg.transform.translation.x = self.x
        tf_msg.transform.translation.y = self.y
        tf_msg.transform.rotation.z = qz
        tf_msg.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(tf_msg)

        # Publish Odometry message
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_footprint"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = w
        self.odom_pub.publish(odom)

    def destroy_node(self):
        # Always command zero velocity on node shutdown
        self.send_wheel_velocities(0.0, 0.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = D1BaseDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()