import json
import time
from pathlib import Path
import rospy
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
rospy.init_node('drive_test_status')
samples = []
commands = []
rospy.Subscriber('/d1/dry_run_cmd_vel', Twist,
                 lambda m: samples.append([time.monotonic(), m.linear.x, m.angular.z]))
rospy.Subscriber('/cmd_vel', Twist, lambda m: commands.append(time.monotonic()))
pub = rospy.Publisher('/robot/button/emergency_state', Bool, queue_size=1)
end = time.monotonic() + 25
while time.monotonic() < end:
    control = Path('/tmp/drive-control.json')
    data = json.loads(control.read_text()) if control.exists() else {}
    if data.get('status', True):
        pub.publish(Bool(data=data.get('pressed', False)))
    time.sleep(.02)
Path('/tmp/drive-samples.json').write_text(json.dumps(dict(samples=samples, hardware_commands=commands)))
