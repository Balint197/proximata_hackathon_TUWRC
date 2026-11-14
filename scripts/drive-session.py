#!/usr/bin/env python2
"""Supervised D1 drive session (floor). Requires --run and a person holding the stop.

Starts gate + independent watchdog, powers and enables motors, activates the
watchdog, then runs ONE ROS 2 command (scripted motion or a Nav2 goal) in the
rootless environment. Any guard, stop press, watchdog trip, time limit, geofence
breach or the command exiting ends the session: motion sources are killed and
motor enable + power are switched off. Never re-arms automatically.

  python2 scripts/drive-session.py --run [--max-seconds 90] [--geofence 3] \
      -- python3 /root/d1-tools/d1_motion.py rotate 90
"""
from __future__ import print_function
import argparse, json, math, os, signal, subprocess, sys, threading, time
import shutil
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
from std_srvs.srv import SetBool
from mot_sbl2360_msgs.msg import MotorState
from stand_startup import safe_to_enable, stop_motion_sources
from session_checks import proximity, within_geofence

parser = argparse.ArgumentParser()
parser.add_argument('--run', action='store_true', required=True)
parser.add_argument('--max-seconds', type=float, default=90.)
parser.add_argument('--geofence', type=float, default=3.)
parser.add_argument('--idle-timeout', type=float, default=1.5)
parser.add_argument('--label', default='session')
parser.add_argument('--scan-guard', choices=['forward', 'full', 'off'], default='forward',
                    help='forward: stop for obstacles in the path while driving forward (default); '
                         'full: also side contact and turning sweep; off: physical stop/watchdog only')
parser.add_argument('--stop-ahead', type=float, default=.33,
                    help='forward guard: stop for anything this far beyond the front bumper (m); '
                         'lower it only for a deliberate approach to a target')
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[:1] == ['--'] else args.command
if not command: parser.error('a ROS 2 command is required after --')
if not 0 < args.max_seconds <= 300: parser.error('max-seconds must be in (0, 300]')
if not .05 <= args.stop_ahead <= 1.: parser.error('stop-ahead must be in [0.05, 1] m')
if not 0 < args.geofence <= 6: parser.error('geofence must be in (0, 6] m')
if not 0 < args.idle_timeout <= 3: parser.error('idle-timeout must be in (0, 3] s')

rospy.init_node('d1_drive_session', disable_signals=True)
repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tools = os.path.expanduser(os.environ.get('D1_ROS2_ROOTFS', '~/.local/share/d1-ros2/rootfs')) + '/root/d1-tools/'
for name in ['d1_motion.py', 'd1_goto.py']:
    if os.path.exists(repo + '/scripts/' + name): shutil.copy(repo + '/scripts/' + name, tools + name)
if os.path.exists(repo + '/config/places.yaml'): shutil.copy(repo + '/config/places.yaml', tools + 'places.yaml')
start = time.time(); events = []; lock = threading.Lock(); throttle = {}
state = dict(button=None, button_time=0, actual_time=0, x=0, z=0, power=None, power_time=0,
             controllable=False, controllable_time=0, watchdog_prepared=False,
             watchdog_ready=False, watchdog_time=0, watchdog_tripped=False,
             scan_time=0, prox=None, gate_z=0., gate_x=0., odom_time=0, start_pose=None, pose=None)
abort = threading.Event()

def record(kind, period=0, **data):
    now = time.time()
    if period and now - throttle.get(kind, 0) < period: return
    throttle[kind] = now
    data.update(kind=kind, t=round(now - start, 3))
    with lock: events.append(data)

def guard(reason, **data):
    first = not abort.is_set()
    abort.set()   # set first: logging must never be able to swallow a trip
    if first:
        try:
            record('guard_trip', reason=reason, **data)
            print(json.dumps(dict(event='guard_trip', reason=reason)), file=sys.stderr)
        except Exception:
            pass

def scan(msg):
    age = time.time() - msg.header.stamp.to_sec()
    if age < -.05 or age > .3: guard('scan_timestamp', age=age)
    # Sweep radius applies while a turn is commanded or measured.
    rotating = abs(state['gate_z']) > .045 or abs(state['z']) > .06
    forward = state['gate_x'] > .005 or state['x'] > .02
    p = proximity(msg.ranges, msg.angle_min, msg.angle_increment, msg.range_min, msg.range_max,
                  rotating, forward, args.stop_ahead)
    state.update(prox=p, scan_time=time.time())
    record('scan', .2, **p)
    if p['stop'] and (args.scan_guard == 'full' or
                      (args.scan_guard == 'forward' and p['reason'] == 'obstacle_ahead')):
        guard('scan_' + p['reason'], scan=p)

def odometry(msg):
    age = time.time() - msg.header.stamp.to_sec()
    if age < -.05 or age > .3: guard('odom_timestamp', age=age)
    q = msg.pose.pose.orientation
    pose = (msg.pose.pose.position.x, msg.pose.pose.position.y,
            math.atan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z)))
    if state['start_pose'] is None: state['start_pose'] = pose
    state.update(pose=pose, odom_time=time.time())
    record('odom', .1, x=pose[0], y=pose[1], yaw=pose[2])
    if not within_geofence(state['start_pose'], pose, args.geofence): guard('geofence', pose=pose)

def velocity(msg):
    state.update(x=msg.linear.x, z=msg.angular.z, actual_time=time.time())
    record('actual', .1, x=msg.linear.x, z=msg.angular.z)
    if abs(msg.angular.z) > .60 or abs(msg.linear.x) > .30:  # feedback overshoots ~2x on turns
        guard('velocity_limit', x=msg.linear.x, z=msg.angular.z)

def button(msg):
    state.update(button=msg.data, button_time=time.time())
    if msg.data: record('button', value=True); guard('physical_stop')

def controllable(msg):
    state.update(controllable=msg.result, controllable_time=time.time())
    record('controllable', 1., result=msg.result, ui_srv_call=msg.ui_srv_call, no_error=msg.no_error)

def wd_prepared(msg): state['watchdog_prepared'] = msg.data
def wd_ready(msg): state.update(watchdog_ready=msg.data, watchdog_time=time.time())
def wd_tripped(msg):
    if msg.data and not state['watchdog_tripped']: record('watchdog_tripped')
    state['watchdog_tripped'] = msg.data
def power(msg):
    if msg.data != state['power']: record('power', value=msg.data)
    state.update(power=msg.data, power_time=time.time())

def command_seen(msg):
    caller = msg._connection_header.get('callerid')
    if caller == '/d1_drive_gate':
        state['gate_z'] = msg.angular.z; state['gate_x'] = msg.linear.x
        record('gate_cmd', .1, x=msg.linear.x, z=msg.angular.z)
        if msg.linear.x < 0: guard('reverse_command', x=msg.linear.x)  # laser cannot see behind

subs = [rospy.Subscriber('/d1/drive_supervisor_prepared', Bool, wd_prepared),
        rospy.Subscriber('/d1/drive_supervisor_ready', Bool, wd_ready),
        rospy.Subscriber('/d1/drive_supervisor_tripped', Bool, wd_tripped),
        rospy.Subscriber('/robot/motor/controllable_state', MotorState, controllable),
        rospy.Subscriber('/robot/motor/actual_vel', Twist, velocity),
        rospy.Subscriber('/robot/button/emergency_state', Bool, button),
        rospy.Subscriber('/robot/motor_power', Bool, power),
        rospy.Subscriber('/robot/scan', LaserScan, scan, queue_size=1),
        rospy.Subscriber('/robot/odom', Odometry, odometry, queue_size=1),
        rospy.Subscriber('/cmd_vel', Twist, command_seen)]
zero = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
activate_watchdog = rospy.Publisher('/d1/drive_supervisor_activate', Bool, queue_size=1)
services = {}
for name in ['/robot/motor/enable_srv', '/gpio/motorpower_srv']:
    rospy.wait_for_service(name, timeout=4)
    services[name] = rospy.ServiceProxy(name, SetBool)

def service(name, value):
    try:
        result = services[name](value)
        record('service', name=name, value=value, success=result.success)
        return result
    except Exception as exc:
        record('service_error', name=name, value=value, error=str(exc)); raise

def cleanup():
    workers = []
    def disable(name):
        try: service(name, False)
        except Exception: pass
    for name in ['/robot/motor/enable_srv', '/gpio/motorpower_srv']:
        w = threading.Thread(target=disable, args=(name,)); w.daemon = True; w.start(); workers.append(w)
    deadline = time.time() + 1.5
    while time.time() < deadline:
        zero.publish(Twist())
        if all(not w.is_alive() for w in workers): break
        time.sleep(.02)

# Deadline failsafe: separate process. Fires at the hard deadline OR as soon as
# this supervisor process disappears (crash/kill). Never enables anything.
failsafe_code = '''import os,sys,time,rospy
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool
parent=int(sys.argv[1]); deadline=time.time()+float(sys.argv[2])
rospy.init_node("d1_session_deadline",anonymous=True,disable_signals=True)
p=rospy.Publisher("/cmd_vel",Twist,queue_size=1)
def alive():
    try: os.kill(parent,0); return True
    except OSError: return False
while time.time()<deadline and alive(): time.sleep(.05)
for i in range(20): p.publish(Twist()); time.sleep(.02)
for name in ["/robot/motor/enable_srv","/gpio/motorpower_srv"]:
    try: rospy.ServiceProxy(name,SetBool)(False)
    except Exception: pass
'''

stop_requested = []
def on_signal(signum, frame):
    stop_requested.append(signum); guard('operator_signal', signum=signum)
signal.signal(signal.SIGINT, on_signal); signal.signal(signal.SIGTERM, on_signal)

children = []; reason = 'not_started'; gate = stimulus = watchdog = None
try:
    time.sleep(1.2)
    now = time.time()
    assert state['button'] is False and now - state['button_time'] < .3, 'stop status unavailable/pressed'
    assert now - state['actual_time'] < .3 and state['x'] == 0 and state['z'] == 0, 'feedback stale/nonzero'
    assert state['power'] is False, 'motor power already on'
    assert state['prox'] and now - state['scan_time'] < .3, 'scan missing'
    assert args.scan_guard != 'full' or not state['prox']['stop'], 'surroundings not clear: %s' % (state['prox'],)
    assert state['pose'] is not None and now - state['odom_time'] < .3, 'odometry missing'
    import rosgraph, rosnode
    master = rosgraph.Master(rospy.get_name())
    names = dict(master.getSystemState()[0]).get('/cmd_vel', [])
    for owned in ['/d1_drive_gate', '/d1_drive_watchdog']:
        if owned in names and not rosnode.rosnode_ping(owned, max_count=1, verbose=False):
            rosnode.cleanup_master_blacklist(master, [owned]); record('removed_dead_owned_registration', node=owned)
    names = dict(master.getSystemState()[0]).get('/cmd_vel', [])
    names = [n for n in names if not n.startswith('/d1_session_deadline')]
    record('preflight', publishers=names, scan=state['prox'])
    assert set(names).issubset(set(['/mot_sbl2360_driver', rospy.get_name()])), 'unexpected /cmd_vel publisher %s' % names
    subprocess.Popen([sys.executable, '-c', failsafe_code, str(os.getpid()), str(args.max_seconds + 15)],
                     stdout=open('/tmp/d1-session-deadline.log', 'w'), stderr=subprocess.STDOUT,
                     preexec_fn=os.setsid)
    gate = subprocess.Popen(['bash', repo + '/scripts/run-drive-gate.sh', '--hardware'],
                            stdout=open('/tmp/d1-session-gate.log', 'w'), stderr=subprocess.STDOUT,
                            preexec_fn=os.setsid); children.append(gate)
    time.sleep(2)
    assert gate.poll() is None and not abort.is_set(), 'gate exited or guard tripped'
    watchdog = subprocess.Popen(['bash', repo + '/scripts/run-drive-watchdog.sh', '--hardware',
                                 '--idle-timeout', str(args.idle_timeout)],
                                stdout=open('/tmp/d1-session-watchdog.log', 'w'), stderr=subprocess.STDOUT,
                                preexec_fn=os.setsid); children.append(watchdog)
    deadline = time.time() + 4
    while not state['watchdog_prepared']:
        if watchdog.poll() is not None: raise RuntimeError('watchdog exited')
        if abort.is_set(): raise RuntimeError('guard while awaiting watchdog')
        if time.time() > deadline: raise RuntimeError('watchdog not prepared')
        time.sleep(.02)
    service('/gpio/motorpower_srv', True)
    deadline = time.time() + .3
    while not safe_to_enable(state, time.time(), abort.is_set(), watchdog.poll() is None):
        if abort.is_set() or state['watchdog_tripped']: raise RuntimeError('post-power check denied enable')
        if time.time() > deadline: raise RuntimeError('post-power fresh status not confirmed')
        time.sleep(.01)
    service('/robot/motor/enable_srv', True)
    deadline = time.time() + 1
    while not (state['controllable'] and time.time() - state['controllable_time'] < .3):
        if abort.is_set(): raise RuntimeError('guard during enable')
        if time.time() > deadline: raise RuntimeError('controllable state not confirmed')
        time.sleep(.05)
    deadline = time.time() + 1
    while not (time.time() - state['button_time'] < .15 and not state['button']):
        if abort.is_set() or time.time() > deadline: raise RuntimeError('stop status not fresh after enable')
        time.sleep(.02)
    activate_watchdog.publish(Bool(data=True))
    deadline = time.time() + 1
    while not (state['watchdog_ready'] and time.time() - state['watchdog_time'] < .15):
        if state['watchdog_tripped'] or time.time() > deadline: raise RuntimeError('watchdog activation failed')
        time.sleep(.02)
    record('session_ready')
    print(json.dumps(dict(event='session_ready', t=time.time() - start)), file=sys.stderr)
    stimulus = subprocess.Popen(['bash', repo + '/scripts/ros2-shell.sh', '/bin/bash', '-ec',
                                 'source /opt/ros/humble/setup.bash; exec "$@"', 'bash'] + command,
                                stdout=open('/tmp/d1-session-stimulus.log', 'w'), stderr=subprocess.STDOUT,
                                preexec_fn=os.setsid); children.append(stimulus)
    hard_deadline = time.time() + args.max_seconds
    while True:
        now = time.time()
        if abort.is_set(): reason = 'guard'; break
        if stimulus.poll() is not None:
            reason = 'command_finished' if stimulus.returncode == 0 else 'command_failed_%d' % stimulus.returncode; break
        if state['watchdog_tripped']: reason = 'watchdog_trip'; break
        if watchdog.poll() is not None: reason = 'watchdog_exited'; break
        if gate.poll() is not None: reason = 'gate_exited'; break
        if now > hard_deadline: reason = 'max_seconds'; break
        if (now - state['scan_time'] > .3 or now - state['odom_time'] > .3 or now - state['actual_time'] > .3 or
                now - state['button_time'] > .3 or now - state['controllable_time'] > .3 or
                not state['controllable']):
            reason = 'stale_or_uncontrollable'; break
        time.sleep(.01)
except Exception as exc:
    reason = 'startup_error: %s' % exc
finally:
    trip_sent = stop_motion_sources(stimulus, gate, lambda: activate_watchdog.publish(Bool(data=False)),
                                    lambda child: os.killpg(child.pid, signal.SIGKILL))
    record('stop_motion_sources', watchdog_trip_sent=trip_sent)
    cleanup()
    time.sleep(.5)
    for child in children:
        if child.poll() is None:
            try: os.killpg(child.pid, signal.SIGINT)
            except OSError: pass
    deadline = time.time() + 3
    while any(c.poll() is None for c in children) and time.time() < deadline: time.sleep(.05)
    for child in children:
        if child.poll() is None:
            try: os.killpg(child.pid, signal.SIGKILL)
            except OSError: pass
    try:
        import rosgraph, rosnode
        for node in ['/d1_drive_gate', '/d1_drive_watchdog']:
            if not rosnode.rosnode_ping(node, max_count=1, verbose=False):
                rosnode.cleanup_master_blacklist(rosgraph.Master(rospy.get_name()), [node])
    except Exception as exc:
        record('registration_cleanup_error', error=str(exc))
    time.sleep(1)
    start_pose, pose = state['start_pose'], state['pose']
    summary = dict(label=args.label, command=command, reason=reason,
                   guards=[e for e in events if e['kind'] == 'guard_trip'],
                   duration_s=round(time.time() - start, 2), final_power=state['power'],
                   final_speed=dict(x=state['x'], z=state['z']),
                   odom_start=start_pose, odom_end=pose,
                   odom_distance_m=(math.hypot(pose[0]-start_pose[0], pose[1]-start_pose[1])
                                    if start_pose and pose else None))
    stamp = time.strftime('%Y%m%dT%H%M%S')
    os.path.isdir(repo + '/docs/evidence/sessions') or os.makedirs(repo + '/docs/evidence/sessions')
    path = '%s/docs/evidence/sessions/%s-%s.json' % (repo, stamp, args.label)
    with open(path, 'w') as stream: json.dump(dict(summary=summary, events=events), stream, indent=1)
    summary['evidence'] = path
    print(json.dumps(summary))
