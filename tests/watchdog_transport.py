"""Private-master test: independent disable RPCs and source-specific expiry."""
import json
import subprocess
import sys
import time
import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_srvs.srv import SetBool, SetBoolResponse
rospy.init_node('d1_drive_gate')  # Fake the adapter, on the private master only.
state = dict(ready=False, trip=False, prepared=False)
powered = False
calls = []
zeros = []
def blocked_enable(req):
    calls.append(('enable', req.data, time.monotonic()))
    time.sleep(2)
    return SetBoolResponse(success=False, message='false')
def power_off(req):
    calls.append(('power', req.data, time.monotonic()))
    return SetBoolResponse(success=True, message='well done')
services = [rospy.Service('/robot/motor/enable_srv', SetBool, blocked_enable),
            rospy.Service('/gpio/motorpower_srv', SetBool, power_off)]
cmd = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
stop = rospy.Publisher('/robot/button/emergency_state', Bool, queue_size=1)
power = rospy.Publisher('/robot/motor_power', Bool, queue_size=1)
activate = rospy.Publisher('/d1/drive_supervisor_activate', Bool, queue_size=1)
subs = [rospy.Subscriber('/d1/drive_supervisor_prepared', Bool, lambda m: state.update(prepared=m.data)),
        rospy.Subscriber('/d1/drive_supervisor_ready', Bool, lambda m: state.update(ready=m.data)),
        rospy.Subscriber('/d1/drive_supervisor_tripped', Bool, lambda m: state.update(trip=m.data)),
        rospy.Subscriber('/cmd_vel', Twist, lambda m: zeros.append(time.monotonic())
                         if m._connection_header.get('callerid') == '/d1_drive_watchdog' else None)]
def pump(duration, gate=True):
    end = time.monotonic() + duration
    while time.monotonic() < end:
        stop.publish(Bool(data=False)); power.publish(Bool(data=powered))
        if gate: cmd.publish(Twist())
        time.sleep(.02)
results = []
for hardware, shutdown_test in ((False, False), (True, False), (True, True)):
    state.update(ready=False, trip=False, prepared=False); powered = False; calls[:] = []; zeros[:] = []
    log = open('/tmp/watchdog-runtime-'+str(hardware)+'.log', 'w')
    child = subprocess.Popen([sys.executable, '/root/d1-tools/drive-watchdog.py'] +
                             (['--hardware'] if hardware else []), stdout=log, stderr=log)
    try:
        deadline = time.monotonic()+4
        while not state['prepared'] and time.monotonic()<deadline: pump(.05)
        assert state['prepared'], 'supervisor did not prepare'
        powered = True; pump(.1); activate.publish(Bool(data=True))
        while not state['ready'] and time.monotonic()<deadline: pump(.05)
        assert state['ready'], 'supervisor never became ready'
        if shutdown_test:
            child.terminate(); child.wait(timeout=3)
            pump(.1)
            assert {c[0] for c in calls} == {'enable', 'power'}, ('shutdown disable missing', calls)
            assert all(not c[1] for c in calls)
            results.append(dict(hardware_mode=True, healthy_shutdown=True, passed=True))
            continue
        loss = time.monotonic(); pump(.65, gate=False)
        assert state['trip'] and not state['ready'], 'loss did not latch trip'
        if hardware:
            power_calls = [c for c in calls if c[0]=='power']
            assert power_calls and power_calls[0][2]-loss < .5, calls
            assert any(c[0]=='enable' for c in calls), calls
            assert zeros and zeros[0]-loss < .5, 'missing immediate zero'
            assert all(not c[1] for c in calls), 'enable request emitted'
        else:
            assert not calls and not zeros, 'dry-run affected hardware interfaces'
        pump(.2)
        assert state['trip'] and not state['ready'], 'recovery auto-rearmed'
        results.append(dict(hardware_mode=hardware, passed=True,
                            disable_requests=len(calls), zero_messages=len(zeros)))
    finally:
        child.terminate(); child.wait(timeout=3); log.close()
        pump(.1)
print(json.dumps(dict(isolated=True, blocked_enable_did_not_block_power_off=True,
                      results=results), indent=2))
