"""Bounded ROS 2 stand stimulus. Does not enable motor power."""
import json
import time
import sys
import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
floor_long = sys.argv[1:] == ["--floor-long"]
floor_test = sys.argv[1:] == ["--floor"] or floor_long
if sys.argv[1:] and not floor_test: raise SystemExit("Unknown mode")
rclpy.init()
node = rclpy.create_node('d1_stand_stimulus')
cmd = node.create_publisher(Twist, '/cmd_vel', 1)
arm = node.create_publisher(Bool, '/d1/drive_arm', 1)
state = {'armed': False}
sub = node.create_subscription(Bool, '/d1/drive_armed',
                               lambda m: state.update(armed=m.data), 1)
def log(event):
    print(json.dumps(dict(event=event, wall=time.time(), monotonic=time.monotonic())), flush=True)
def spin(duration):
    end = time.monotonic() + duration
    while time.monotonic() < end:
        rclpy.spin_once(node, timeout_sec=.02)
try:
    spin(2.)
    assert cmd.get_subscription_count() == 1, 'expected exactly one ROS 2 command subscriber'
    arm.publish(Bool(data=True)); spin(.15)
    assert state['armed'], 'gate failed to arm'
    log('command_start')
    end = time.monotonic() + (2. if floor_long else .8 if floor_test else 1.5)
    while time.monotonic() < end and state['armed']:
        msg = Twist()
        if floor_test: msg.linear.x = .05
        else: msg.angular.z = .08
        cmd.publish(msg)
        rclpy.spin_once(node, timeout_sec=.02)
    log('command_stream_end')
    spin(3.)
    assert not state['armed'], 'gate did not latch disarmed on timeout'
    log('gate_disarmed_after_command_loss')
finally:
    arm.publish(Bool(data=False)); cmd.publish(Twist()); spin(.15)
    node.destroy_node(); rclpy.shutdown()
