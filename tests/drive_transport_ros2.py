import json
import time
from pathlib import Path
import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
rclpy.init()
node = rclpy.create_node('drive_test_commands')
cmd = node.create_publisher(Twist, '/cmd_vel', 1)
arm = node.create_publisher(Bool, '/d1/drive_arm', 1)
phases = []
def control(**data):
    path = Path('/tmp/drive-control-next.json')
    path.write_text(json.dumps(data))
    path.replace('/tmp/drive-control.json')
def run(name, duration, command=False):
    start = time.monotonic()
    while time.monotonic() - start < duration:
        if command:
            msg = Twist(); msg.linear.x = 1.; msg.angular.z = -1.
            cmd.publish(msg)
        rclpy.spin_once(node, timeout_sec=.02)
    phases.append(dict(name=name, start=start, end=time.monotonic()))
def rearm():
    arm.publish(Bool(data=True))
    run('arming', .15)
control(status=True, pressed=False)
run('discovery', 3)
assert cmd.get_subscription_count() == 1, 'drive gate not discovered'
run('startup', .7, True)
rearm(); run('bounded', .7, True)
run('timeout', .7)
run('timeout_latched', .5, True)
rearm(); run('before_stop', .5, True)
control(status=True, pressed=True); run('pressed', .6, True)
control(status=True, pressed=False); run('released_latched', .6, True)
rearm(); run('rearmed', .5, True)
control(status=False); run('stale_status', .8, True)
control(status=True, pressed=False); run('status_recovered_latched', .6, True)
Path('/tmp/drive-phases.json').write_text(json.dumps(phases))
node.destroy_node(); rclpy.shutdown()
