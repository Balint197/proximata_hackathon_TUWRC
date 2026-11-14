"""Send the D1 to a named place with Nav2 (ROS 2). Run inside drive-session.py.

    python3 d1_goto.py door            # place from /root/d1-tools/places.yaml
    python3 d1_goto.py --xy 2.0 -1.0 0  # explicit map pose x y yaw

Arms the drive gate, sends NavigateToPose to /d1_nav/navigate_to_pose and waits.
If the gate disarms (stop button, command loss) the goal is cancelled and the
exit code is non-zero; the session supervisor then powers the motors off.
"""
import json
import math
import sys
import time
import yaml
import rclpy
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool

PLACES = '/root/d1-tools/places.yaml'


def log(**kw): print(json.dumps(dict(kw, wall=time.time())), flush=True)


def target(argv):
    if argv[:1] == ['--xy']:
        x, y, yaw = (float(v) for v in argv[1:4]); return 'xy', x, y, yaw
    places = yaml.safe_load(open(PLACES))['places']
    p = places[argv[0]]
    return argv[0], float(p['x']), float(p['y']), float(p['yaw'])


def main():
    name, x, y, yaw = target(sys.argv[1:])
    rclpy.init(); node = rclpy.create_node('d1_goto')
    arm = node.create_publisher(Bool, '/d1/drive_arm', 1)
    st = dict(armed=False, seen=False)
    def armed(m):
        st['armed'] = m.data; st['seen'] = True
    node.create_subscription(Bool, '/d1/drive_armed', armed, 1)
    client = ActionClient(node, NavigateToPose, '/d1_nav/navigate_to_pose')
    code = 1; handle = None
    try:
        assert client.wait_for_server(timeout_sec=10.), 'Nav2 navigate_to_pose not available'
        deadline = time.monotonic() + 6
        while (arm.get_subscription_count() < 1 or not st['seen']) and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
        arm.publish(Bool(data=True))
        deadline = time.monotonic() + 1.
        while not st['armed'] and time.monotonic() < deadline: rclpy.spin_once(node, timeout_sec=.05)
        assert st['armed'], 'drive gate refused to arm'
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped(); goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        goal.pose.pose.position.x = x; goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2); goal.pose.pose.orientation.w = math.cos(yaw / 2)
        log(event='goal_sent', place=name, x=x, y=y, yaw=yaw)
        fut = client.send_goal_async(goal, feedback_callback=lambda f: st.update(
            remaining=f.feedback.distance_remaining))
        rclpy.spin_until_future_complete(node, fut, timeout_sec=5.)
        handle = fut.result()
        assert handle is not None and handle.accepted, 'goal rejected'
        result = handle.get_result_async(); last = 0
        while not result.done():
            rclpy.spin_once(node, timeout_sec=.05)
            if not st['armed']:
                raise RuntimeError('drive gate disarmed (stop/command loss)')
            if time.monotonic() - last > 2:
                last = time.monotonic(); log(event='feedback', remaining=st.get('remaining'))
        status = result.result().status
        log(event='result', status=status, succeeded=status == GoalStatus.STATUS_SUCCEEDED)
        code = 0 if status == GoalStatus.STATUS_SUCCEEDED else 2
    except Exception as exc:
        log(event='abort', error=str(exc)); code = 3
        if handle is not None:
            try:
                c = handle.cancel_goal_async(); rclpy.spin_until_future_complete(node, c, timeout_sec=2.)
            except Exception: pass
    finally:
        arm.publish(Bool(data=False))
        end = time.monotonic() + .2
        while time.monotonic() < end: rclpy.spin_once(node, timeout_sec=.05)
        node.destroy_node(); rclpy.shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()
