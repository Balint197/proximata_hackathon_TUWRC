#!/usr/bin/env python2
"""Supervised bounded diagnostic (stand by default); requires explicit --run. Powers off on every exit."""
from __future__ import print_function
import json, os, signal, subprocess, sys, threading, time
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from floor_checks import front_clearance, pose_within_limit, ScanQualityGuard
import math
from std_msgs.msg import Bool
from std_srvs.srv import SetBool
from mot_sbl2360_msgs.msg import Duplex, MotorState
from stand_startup import safe_to_enable, stop_motion_sources
floor_long = sys.argv[1:] == ['--run','--floor-long']
floor_test = sys.argv[1:] == ['--run', '--floor'] or floor_long
watchdog_test = sys.argv[1:] == ['--run', '--gate-loss', '--watchdog'] or floor_test
gate_loss = sys.argv[1:] in (['--run','--gate-loss'], ['--run','--gate-loss','--watchdog'])
if sys.argv[1:] != ['--run'] and not gate_loss and not floor_test:
    raise SystemExit('Requires --run and physical stand/stop supervision')
rospy.init_node('d1_ros2_stand_supervisor', disable_signals=True)
repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
start = time.time(); events = []; lock = threading.Lock()
state = dict(button=None, button_time=0, actual_time=0, x=0, z=0, power=None, power_time=0, controllable=False, controllable_time=0, watchdog_prepared=False, watchdog_ready=False, watchdog_time=0, watchdog_tripped=False, scan_time=0, odom_time=0, front=None, initial_pose=None, pose=None)
abort = threading.Event()
scan_quality_guard=ScanQualityGuard()
def record(kind, **data):
    data.update(kind=kind, t=time.time()-start)
    with lock: events.append(data)
def guard(reason, **data):
    if not abort.is_set(): record('guard_trip', reason=reason, **data)
    abort.set()
def scan(msg):
    age=time.time()-msg.header.stamp.to_sec()
    if age<-.05 or age>.3: guard('scan_timestamp',age=age)
    result=front_clearance(msg.ranges,msg.angle_min,msg.angle_increment,msg.range_min,msg.range_max)
    state.update(front=result,scan_time=time.time())
    record('floor_scan', **result)
    if scan_quality_guard.stop(front_clearance(msg.ranges,msg.angle_min,msg.angle_increment,msg.range_min,msg.range_max,.5),time.time()):
        guard('forward_clearance', **result)
def odometry(msg):
    age=time.time()-msg.header.stamp.to_sec()
    if age<-.05 or age>.3: guard('odom_timestamp',age=age)
    q=msg.pose.pose.orientation
    pose=(msg.pose.pose.position.x,msg.pose.pose.position.y,
          math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
    if state['initial_pose'] is None: state['initial_pose']=pose
    state.update(pose=pose,odom_time=time.time())
    record('floor_odom', x=pose[0],y=pose[1],yaw=pose[2],frame=msg.header.frame_id,child=msg.child_frame_id)
    if not pose_within_limit(state['initial_pose'],pose): guard('pose_limit',pose=pose)
def velocity(msg):
    state.update(x=msg.linear.x, z=msg.angular.z, actual_time=time.time())
    record('actual', x=msg.linear.x, z=msg.angular.z)
    if abs(msg.angular.z) > .25 or abs(msg.linear.x) > .10: guard('velocity_limit',x=msg.linear.x,z=msg.angular.z)
def button(msg):
    state.update(button=msg.data, button_time=time.time())
    record('button', value=msg.data)
    if msg.data: guard('physical_stop')
def controllable(msg):
    state.update(controllable=msg.result, controllable_time=time.time())
    record('controllable', result=msg.result, emg_release=msg.emg_release,
           no_fall=msg.no_fall, ui_srv_call=msg.ui_srv_call,
           no_error=msg.no_error, firmware_ver_corr=msg.firmware_ver_corr)
def watchdog_prepared(msg):
    state['watchdog_prepared']=msg.data

def watchdog_ready(msg):
    state.update(watchdog_ready=msg.data, watchdog_time=time.time())
    record('watchdog_ready', value=msg.data)
def watchdog_tripped(msg):
    state['watchdog_tripped']=msg.data
    record('watchdog_tripped', value=msg.data)
def power(msg):
    state.update(power=msg.data,power_time=time.time()); record('power', value=msg.data)
subs = [rospy.Subscriber('/d1/drive_supervisor_prepared', Bool, watchdog_prepared),
        rospy.Subscriber('/d1/drive_supervisor_ready', Bool, watchdog_ready),
        rospy.Subscriber('/d1/drive_supervisor_tripped', Bool, watchdog_tripped),
        rospy.Subscriber('/robot/motor/controllable_state', MotorState, controllable),
        rospy.Subscriber('/robot/motor/actual_vel', Twist, velocity),
        rospy.Subscriber('/robot/button/emergency_state', Bool, button),
        rospy.Subscriber('/robot/motor_power', Bool, power)]
if floor_test:
    subs.extend([rospy.Subscriber('/robot/scan', LaserScan, scan),
                 rospy.Subscriber('/robot/odom', Odometry, odometry)])
for topic in ['/cmd_vel', '/filtered_cmd_vel']:
    subs.append(rospy.Subscriber(topic, Twist,
        lambda msg, name=topic: record(name, x=msg.linear.x, z=msg.angular.z,
            caller=msg._connection_header.get('callerid'))))
for topic in ['actual_rpm','encoder','rpm']:
    subs.append(rospy.Subscriber('/robot/motor/'+topic, Duplex,
        lambda msg, name=topic: record(name, left=msg.left, right=msg.right)))
zero = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
activate_watchdog=rospy.Publisher('/d1/drive_supervisor_activate', Bool, queue_size=1)
services = {}
for name in ['/robot/motor/enable_srv','/gpio/motorpower_srv']:
    rospy.wait_for_service(name, timeout=4)
    services[name]=rospy.ServiceProxy(name, SetBool)
def service(name, value):
    try:
        result=services[name](value)
        record('service', name=name, value=value, success=result.success, message=result.message)
        return result
    except Exception as exc:
        record('service_error', name=name, value=value, error=str(exc)); raise
def cleanup():
    # Independent calls: a stuck motor-enable RPC must not block power-off.
    workers=[]
    def disable(name):
        try: service(name, False)
        except Exception: pass
    for name in ['/robot/motor/enable_srv','/gpio/motorpower_srv']:
        worker=threading.Thread(target=disable,args=(name,)); worker.daemon=True
        worker.start(); workers.append(worker)
    deadline=time.time()+1.5
    while time.time()<deadline:
        zero.publish(Twist())
        if all(not worker.is_alive() for worker in workers): break
        time.sleep(.02)
# Separate bounded supervisor process: never enables anything. Survives this process exiting.
failsafe_code = '''import time,rospy
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool
rospy.init_node("d1_stand_deadline",disable_signals=True)
p=rospy.Publisher("/cmd_vel",Twist,queue_size=1)
time.sleep(14)
for i in range(20): p.publish(Twist()); time.sleep(.02)
for name in ["/robot/motor/enable_srv","/gpio/motorpower_srv"]:
 try: rospy.ServiceProxy(name,SetBool)(False)
 except Exception: pass
'''
children=[]; reason='not_started'; enabled=False
gate=None; stimulus=None; watchdog=None
try:
    time.sleep(1)
    assert state['button'] is False and time.time()-state['button_time'] < .3, 'stop status unavailable/pressed'
    assert time.time()-state['actual_time'] < .3 and state['x']==0 and state['z']==0, 'feedback stale/nonzero'
    assert state['power'] is False and rospy.get_param('/mot_sbl2360_driver/motor_enable') is False, 'motors not initially disabled'
    if floor_test:
        assert state['front'] and state['front']['clear'] and time.time()-state['scan_time']<.3, 'forward clearance missing'
        assert state['pose'] is not None and time.time()-state['odom_time']<.3, 'odometry missing'
    import rosgraph
    pubs=rosgraph.Master(rospy.get_name()).getSystemState()[0]
    names=dict(pubs).get('/cmd_vel',[])
    # Crash-injection tests can leave dead registrations. Never remove a live peer.
    import rosnode
    for owned in ['/d1_drive_gate','/d1_drive_watchdog','/d1_stand_deadline']:
        if owned in names and not rosnode.rosnode_ping(owned,max_count=1,verbose=False):
            rosnode.cleanup_master_blacklist(rosgraph.Master(rospy.get_name()),[owned])
            record('removed_dead_owned_registration',node=owned)
    names=dict(rosgraph.Master(rospy.get_name()).getSystemState()[0]).get('/cmd_vel',[])
    record('preflight_publishers', nodes=names)
    assert set(names).issubset(set(['/mot_sbl2360_driver',rospy.get_name()])), 'unexpected command publisher'
    subprocess.Popen([sys.executable,'-c',failsafe_code],stdout=open('/tmp/d1-stand-deadline.log','w'),stderr=subprocess.STDOUT,preexec_fn=os.setsid)
    gate_log=open('/tmp/d1-live-gate.log','w')
    gate=subprocess.Popen(['bash',repo+'/scripts/run-drive-gate.sh','--hardware'],stdout=gate_log,stderr=subprocess.STDOUT,preexec_fn=os.setsid); children.append(gate)
    time.sleep(2)
    assert gate.poll() is None and not abort.is_set(), 'gate exited or a recorded safety guard tripped'
    watchdog=None
    if watchdog_test:
        watchdog_log=open('/tmp/d1-live-watchdog.log','w')
        watchdog=subprocess.Popen(['bash',repo+'/scripts/run-drive-watchdog.sh','--hardware'],
            stdout=watchdog_log,stderr=subprocess.STDOUT,preexec_fn=os.setsid)
        children.append(watchdog)
        ready_deadline=time.time()+3
        while time.time()<ready_deadline:
            if watchdog.poll() is not None: raise RuntimeError('watchdog exited')
            if state['watchdog_prepared']: break
            if abort.is_set(): raise RuntimeError('stop pressed while awaiting watchdog')
            time.sleep(.02)
        else: raise RuntimeError('watchdog not ready')
    service('/gpio/motorpower_srv',True)
    if watchdog_test:
        ready_deadline=time.time()+.3
        while time.time()<ready_deadline:
            if abort.is_set() or state['watchdog_tripped'] or watchdog.poll() is not None:
                raise RuntimeError('post-power safety check denied motor enable')
            if safe_to_enable(state, time.time(), False, True): break
            time.sleep(.01)
        else: raise RuntimeError('post-power fresh status not confirmed')
    if abort.is_set(): raise RuntimeError('stop or guard during power-on RPC')
    service('/robot/motor/enable_srv',True); enabled=True
    enable_deadline=time.time()+1
    while time.time()<enable_deadline:
        value=rospy.get_param('/mot_sbl2360_driver/motor_enable')
        record('enable_param', value=value)
        if state['controllable'] and time.time()-state['controllable_time']<.3: break
        if abort.is_set(): raise RuntimeError('stop or speed guard during enable')
        time.sleep(.05)
    else: raise RuntimeError('live controllable state did not confirm within one second')
    if watchdog_test:
        # Wait for GPIO telemetry to recover after its blocking power relay call.
        ready_deadline=time.time()+1
        while time.time()<ready_deadline:
            if time.time()-state['button_time']<.15 and not state['button']: break
            if abort.is_set(): raise RuntimeError('stop during startup')
            time.sleep(.02)
        activate_watchdog.publish(Bool(data=True))
        ready_deadline=time.time()+1
        while time.time()<ready_deadline:
            if state['watchdog_tripped']: raise RuntimeError('watchdog tripped before motion')
            if state['watchdog_ready'] and time.time()-state['watchdog_time']<.15: break
            time.sleep(.02)
        else: raise RuntimeError('watchdog activation failed')
    command_log=open('/tmp/d1-stand-stimulus.log','w')
    stimulus=subprocess.Popen(['bash',repo+'/scripts/ros2-shell.sh','/bin/bash','-ec',
        'source /opt/ros/humble/setup.bash; exec python3 /root/d1-tools/stand-ros2-command.py' + (' --floor-long' if floor_long else ' --floor' if floor_test else '')],stdout=command_log,stderr=subprocess.STDOUT,preexec_fn=os.setsid); children.append(stimulus)
    deadline=time.time()+9
    killed_at=None
    while stimulus.poll() is None and time.time()<deadline:
        if abort.is_set(): reason='physical_stop_or_motion_clearance_guard'; break
        if floor_test and (time.time()-state['scan_time']>.3 or time.time()-state['odom_time']>.3):
            reason='stale_floor_sensors'; break
        if watchdog_test and killed_at is not None and state['watchdog_tripped']:
            if state['power'] is False:
                reason='independent_watchdog_power_off'; break
            if time.time()-killed_at>1:
                reason='watchdog_trip_power_unconfirmed'; break
        if watchdog is not None and watchdog.poll() is not None:
            reason='watchdog_exited'; break
        if (time.time()-state['actual_time']>.3 or time.time()-state['button_time']>.3 or
                time.time()-state['controllable_time']>.3 or (not state['controllable'] and
                not (watchdog_test and killed_at is not None and state['watchdog_tripped']))):
            reason='stale_feedback'; break
        if gate_loss and killed_at is None:
            command_log.flush()
            try:
                with open('/tmp/d1-stand-stimulus.log') as log:
                    markers=[json.loads(line) for line in log if line.strip()]
                began=next((v['wall'] for v in markers if v['event']=='command_start'),None)
            except (IOError,ValueError): began=None
            if began is not None and time.time()-began>=.7:
                record('injected_gate_process_loss')
                os.killpg(gate.pid, signal.SIGKILL)
                killed_at=time.time()
        if gate.poll() is not None and killed_at is None: reason='gate_exited'; break
        if killed_at is not None and time.time()-killed_at>=2:
            reason='gate_loss_observation_complete'; break
        time.sleep(.01)
    else:
        reason='stimulus_complete' if stimulus.poll()==0 else 'stimulus_failed_or_deadline'
finally:
    trip_sent=stop_motion_sources(stimulus,gate,
        lambda: activate_watchdog.publish(Bool(data=False)),
        lambda child: os.killpg(child.pid,signal.SIGKILL))
    record('watchdog_trip_request',success=trip_sent)
    cleanup()
    if children:
        try:
            import rosnode
            rosnode.kill_nodes(['/d1_drive_gate'] + (['/d1_drive_watchdog'] if watchdog_test and
                state['power'] is False and time.time()-state['power_time']<.3 else []))
            deadline=time.time()+2
            while any(c.poll() is None for c in children[:-1]) and time.time()<deadline: time.sleep(.05)
        except Exception as exc: record('gate_shutdown_error', error=str(exc))
    for child in children:
        if child is watchdog and (state['power'] is not False or time.time()-state['power_time']>.3):
            record('watchdog_left_running', reason='power_off_not_confirmed'); continue
        if child is watchdog and child.poll() is None:
            try:
                rosnode.kill_nodes(['/d1_drive_watchdog'])
                shutdown_deadline=time.time()+1
                while child.poll() is None and time.time()<shutdown_deadline: time.sleep(.02)
            except Exception as exc: record('watchdog_shutdown_error',error=str(exc))
        if child.poll() is None:
            try: os.killpg(child.pid, signal.SIGINT)
            except OSError: pass
    if gate is not None:
        try:
            import rosgraph,rosnode
            if not rosnode.rosnode_ping('/d1_drive_gate',max_count=1,verbose=False):
                rosnode.cleanup_master_blacklist(rosgraph.Master(rospy.get_name()),['/d1_drive_gate'])
        except Exception as exc: record('gate_registration_cleanup_error',error=str(exc))
    time.sleep(2)
    result=dict(start_wall=start, reason=reason, events=events, final_power=state['power'],
        motor_enable=rospy.get_param('/mot_sbl2360_driver/motor_enable'),
        final_speed=dict(x=state['x'],z=state['z']),
        limitation=('Supervised short floor diagnostic; physical distance/direction require operator corroboration; no navigation.' if floor_test else 'Supervised gate-process-loss test; vendor self-publication remains present, not independent controller watchdog certification.' if gate_loss else 'Supervised stand test of ROS 2 stream timeout, not gate-process-death or electrical stop certification.'))
    path=repo+('/docs/evidence/ros2-floor-long-2026-11-14.json' if floor_long else
               '/docs/evidence/ros2-floor-odometry-2026-11-14.json' if floor_test else
               '/docs/evidence/ros2-stand-watchdog-2026-11-14.json' if watchdog_test else
               '/docs/evidence/ros2-stand-gate-loss-2026-11-14.json' if gate_loss else
               '/docs/evidence/ros2-stand-command-loss-2026-11-14.json')
    with open(path,'w') as stream: json.dump(result,stream,indent=2)
    print(json.dumps(dict(reason=reason,final_power=result['final_power'],motor_enable=result['motor_enable'],final_speed=result['final_speed'],evidence=path)))
