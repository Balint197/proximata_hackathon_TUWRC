"""Scripted, odometry-closed motion for supervised sessions (ROS 2).

    python3 d1_motion.py rotate 90 forward 0.5 rotate -45

Arms the drive gate, streams commands continuously at 20 Hz (no gaps between
segments so the watchdog idle timer is not hit), stops at the end, disarms.
Exits non-zero if the gate disarms (stop button, timeout) or odometry stalls.
Run only inside drive-session.py. Forward-only: the laser cannot see behind.
"""
import json
import math
import sys
import time
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool

V, W, V_MIN, W_MIN = .15, .20, .03, .05


def parse(argv):
    steps = []
    if len(argv) % 2: raise SystemExit('usage: (rotate DEG | forward M)...')
    for kind, value in zip(argv[::2], argv[1::2]):
        value = float(value)
        if kind == 'rotate' and abs(value) <= 360: steps.append(('rotate', math.radians(value)))
        elif kind == 'forward' and 0 < value <= 2.: steps.append(('forward', value))
        else: raise SystemExit('bad step %s %s' % (kind, value))
    return steps


def yaw_of(q): return math.atan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))
def wrap(a): return math.atan2(math.sin(a), math.cos(a))
def log(**kw): print(json.dumps(dict(kw, wall=time.time())), flush=True)


def main():
    steps = parse(sys.argv[1:])
    rclpy.init(); node = rclpy.create_node('d1_motion')
    cmd = node.create_publisher(Twist, '/cmd_vel', 1)
    arm = node.create_publisher(Bool, '/d1/drive_arm', 1)
    st = dict(armed=False, pose=None, odom_t=0.)
    node.create_subscription(Bool, '/d1/drive_armed', lambda m: st.update(armed=m.data), 1)
    def odom(m):
        p = m.pose.pose
        st.update(pose=(p.position.x, p.position.y, yaw_of(p.orientation)), odom_t=time.monotonic())
    node.create_subscription(Odometry, '/robot/odom', odom, 5)
    def spin(t):
        end = time.monotonic() + t
        while time.monotonic() < end: rclpy.spin_once(node, timeout_sec=.01)
    code = 0
    try:
        deadline = time.monotonic() + 6.
        while (cmd.get_subscription_count() != 1 or st['pose'] is None) and time.monotonic() < deadline: spin(.1)
        count = cmd.get_subscription_count()
        assert count == 1, 'expected exactly the drive gate on /cmd_vel, found %d' % count
        assert st['pose'] is not None, 'no odometry'
        arm.publish(Bool(data=True)); spin(.2)
        assert st['armed'], 'gate refused to arm'
        for kind, target in steps:
            x0, y0, th0 = st['pose']; seg_start = time.monotonic()
            limit = 8. + (abs(target) / W if kind == 'rotate' else target / V) * 2.5
            log(event='segment_start', kind=kind, target=target, pose=st['pose'])
            while True:
                rclpy.spin_once(node, timeout_sec=.05)
                if not st['armed']: raise RuntimeError('gate disarmed (stop/timeout)')
                if time.monotonic() - st['odom_t'] > .3: raise RuntimeError('odometry stale')
                if time.monotonic() - seg_start > limit: raise RuntimeError('segment timeout')
                x, y, th = st['pose']; msg = Twist()
                if kind == 'rotate':
                    remaining = target - wrap(th - th0) if abs(target) < math.pi else None
                    if remaining is None:   # large turns: integrate
                        st.setdefault('acc', 0.); st['acc'] += wrap(th - st.get('last', th0)); st['last'] = th
                        remaining = target - st['acc']
                    if abs(remaining) < .03: break
                    msg.angular.z = math.copysign(max(W_MIN, min(W, abs(remaining) * .6)), remaining)
                else:
                    done = math.hypot(x - x0, y - y0)
                    remaining = target - done
                    if remaining < .02: break
                    msg.linear.x = max(V_MIN, min(V, remaining * .8))
                    # hold heading
                    msg.angular.z = max(-.04, min(.04, -wrap(th - th0) * .8))
                cmd.publish(msg)
            st.pop('acc', None); st.pop('last', None)
            log(event='segment_done', kind=kind, pose=st['pose'])
    except Exception as exc:
        log(event='abort', error=str(exc)); code = 3
    finally:
        for _ in range(5): cmd.publish(Twist()); spin(.04)
        arm.publish(Bool(data=False)); spin(.1)
        log(event='end', pose=st['pose'])
        node.destroy_node(); rclpy.shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()
