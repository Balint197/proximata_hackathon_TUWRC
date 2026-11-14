#!/usr/bin/env python3
"""Independent ROS 1 supervisor. Default dry-run; never enables hardware."""
import argparse
import json
import threading
import time
import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_srvs.srv import SetBool
from drive_watchdog import DriveWatchdog

parser = argparse.ArgumentParser()
parser.add_argument('--hardware', action='store_true')
parser.add_argument('--idle-timeout', type=float, default=.350,
                    help='latch after this long with zero commands following motion (max 3 s)')
args = parser.parse_args()
rospy.init_node('d1_drive_watchdog')
if not 0 < args.idle_timeout <= 3.:
    parser.error('idle timeout must be in (0, 3] s')
policy = DriveWatchdog(args.idle_timeout)
lock = threading.Lock()

def gate(msg):
    with lock:
        policy.gate([msg.linear.x, msg.linear.y, msg.linear.z,
                     msg.angular.x, msg.angular.y, msg.angular.z],
                    msg._connection_header.get('callerid'), time.monotonic())

def stop(msg):
    with lock: policy.stop(msg.data, time.monotonic())

def activate(msg):
    with lock: policy.activate(msg.data, time.monotonic())

def power(msg):
    with lock: policy.power(msg.data, time.monotonic())

subs = [rospy.Subscriber('/d1/drive_supervisor_activate', Bool, activate, queue_size=1),
        rospy.Subscriber('/cmd_vel', Twist, gate, queue_size=1),
        rospy.Subscriber('/robot/button/emergency_state', Bool, stop, queue_size=1),
        rospy.Subscriber('/robot/motor_power', Bool, power, queue_size=1)]
prepared = rospy.Publisher('/d1/drive_supervisor_prepared', Bool, queue_size=1)
ready = rospy.Publisher('/d1/drive_supervisor_ready', Bool, queue_size=1)
tripped = rospy.Publisher('/d1/drive_supervisor_tripped', Bool, queue_size=1, latch=True)
zero = rospy.Publisher('/cmd_vel', Twist, queue_size=1) if args.hardware else None
service_names = ['/robot/motor/enable_srv', '/gpio/motorpower_srv']
workers = {}
last_attempt = {}

def disable(name):
    try:
        rospy.wait_for_service(name, timeout=.3)
        reply = rospy.ServiceProxy(name, SetBool)(False)
        print(json.dumps(dict(event='disable_reply', service=name, request=False,
                              success=reply.success, monotonic=time.monotonic())), flush=True)
    except Exception as exc:
        print(json.dumps(dict(event='disable_error', service=name, error=str(exc))), flush=True)

def disable_outputs():
    if zero is None: return
    try:
        zero.publish(Twist())
    except rospy.ROSException:
        pass  # Disable RPCs must still run after ROS closes publishers.
    now = time.monotonic()
    for name in service_names:
        if ((name not in workers or not workers[name].is_alive()) and
                now - last_attempt.get(name, -1e9) >= 1.):
            last_attempt[name] = now
            worker = threading.Thread(target=disable, args=(name,), daemon=True)
            workers[name] = worker
            worker.start()

shutdown_done = threading.Event()
def shutdown():
    if shutdown_done.is_set(): return
    shutdown_done.set()
    disable_outputs()
    if args.hardware: time.sleep(.2)

rospy.on_shutdown(shutdown)
logged = False
try:
    while not rospy.is_shutdown():
        with lock:
            trip = policy.tick(time.monotonic())
            is_prepared = policy.prepared and policy.reason is None
            is_ready = policy.ready
            reason = policy.reason
        prepared.publish(Bool(data=is_prepared))
        ready.publish(Bool(data=is_ready))
        tripped.publish(Bool(data=trip))
        if trip:
            if not logged:
                print(json.dumps(dict(event='trip', reason=reason,
                                      monotonic=time.monotonic(), hardware=args.hardware)), flush=True)
                logged = True
            disable_outputs()
        time.sleep(.02)
except rospy.ROSException:
    if not shutdown_done.is_set() and not rospy.is_shutdown(): raise
finally:
    # Best effort on orderly shutdown; process/host loss still needs physical stop.
    shutdown()
