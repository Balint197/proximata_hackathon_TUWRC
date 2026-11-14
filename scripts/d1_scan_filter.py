"""Republish /robot/scan with self-hits removed -> /robot/scan_filtered (ROS 2).

Masks returns that fall inside the 58 x 58 cm body outline and the measured
self-sectors (front-right bracket, right-side cable) from session_checks, so the
Nav2 costmaps do not see the robot itself as an obstacle. Masked rays become
+inf (no return) and still clear space up to range_max in the costmap.
"""
import math
import sys
sys.path.insert(0, '/root/d1-tools')
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from session_checks import LASER_X, HALF, SELF_SECTORS


def main():
    rclpy.init()
    node = rclpy.create_node('d1_scan_filter')
    pub = node.create_publisher(LaserScan, '/robot/scan_filtered', qos_profile_sensor_data)
    cache = {}

    def mask_for(msg):
        key = (msg.angle_min, msg.angle_increment, len(msg.ranges))
        if key not in cache:
            cache[key] = [msg.angle_min + i * msg.angle_increment for i in range(len(msg.ranges))]
        return cache[key]

    def callback(msg):
        angles = mask_for(msg)
        ranges = list(msg.ranges)
        for i, (a, r) in enumerate(zip(angles, ranges)):
            if not math.isfinite(r) or r < msg.range_min:
                continue
            if any(lo <= a <= hi and r <= rmax for lo, hi, rmax in SELF_SECTORS):
                ranges[i] = float('inf'); continue
            x = LASER_X + r * math.cos(a); y = r * math.sin(a)
            if abs(x) <= HALF and abs(y) <= HALF:
                ranges[i] = float('inf')
        msg.ranges = ranges
        pub.publish(msg)

    node.create_subscription(LaserScan, '/robot/scan', callback, qos_profile_sensor_data)
    rclpy.spin(node)


if __name__ == '__main__':
    main()
