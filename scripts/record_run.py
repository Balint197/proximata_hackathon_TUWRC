"""Passive recorder for a Nav2 run (ROS 2, read-only: subscribes only).

    python3 record_run.py OUT.json [seconds]

Saves the SLAM map, map->base_link poses (10 Hz), robot speed from odometry,
every Nav2 global plan, and laser scans (in map frame, 2 Hz) until the time
limit or SIGINT/SIGTERM. scripts/render_run.py turns the file into figures.
"""
import json
import math
import signal
import sys
import time
import rclpy
from rclpy.time import Time
import tf2_ros
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from sensor_msgs.msg import LaserScan
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

out, limit = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 180.
rclpy.init(); node = rclpy.create_node('d1_record_run')
buf = tf2_ros.Buffer(); tf2_ros.TransformListener(buf, node)
data = dict(start=time.time(), map=None, poses=[], speed=[], plans=[], scans=[])
stop = dict(now=False)
for s in (signal.SIGINT, signal.SIGTERM): signal.signal(s, lambda *_: stop.update(now=True))


def yaw_of(q): return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def pose():
    try:
        t = buf.lookup_transform('map', 'base_link', Time())
    except Exception:
        return None
    return t.transform.translation.x, t.transform.translation.y, yaw_of(t.transform.rotation)


def on_map(m):
    data['map'] = dict(res=m.info.resolution, w=m.info.width, h=m.info.height,
                       ox=m.info.origin.position.x, oy=m.info.origin.position.y,
                       cells=list(m.data))


def on_plan(m):
    data['plans'].append(dict(t=time.time() - data['start'],
                              xy=[(round(p.pose.position.x, 3), round(p.pose.position.y, 3))
                                  for p in m.poses]))


def on_odom(m):
    data['speed'].append((round(time.time() - data['start'], 3), round(m.twist.twist.linear.x, 3),
                          round(m.twist.twist.angular.z, 3)))


last_scan = dict(t=0.)
def on_scan(m):
    now = time.time()
    if now - last_scan['t'] < .5: return
    p = pose()
    if p is None: return
    last_scan['t'] = now; x0, y0, th = p; lx = .197
    pts = []
    for i, r in enumerate(m.ranges):
        if not (m.range_min < r < 8.): continue
        a = m.angle_min + i * m.angle_increment
        bx, by = lx + r * math.cos(a), r * math.sin(a)
        pts.append((round(x0 + bx * math.cos(th) - by * math.sin(th), 3),
                    round(y0 + bx * math.sin(th) + by * math.cos(th), 3)))
    front = [r for i, r in enumerate(m.ranges)
             if abs(m.angle_min + i * m.angle_increment) < math.radians(3) and m.range_min < r < 8.]
    data['scans'].append(dict(t=now - data['start'], pose=p, pts=pts,
                              front=min(front) if front else None))


latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
node.create_subscription(OccupancyGrid, '/map', on_map, latched)
node.create_subscription(Path, '/d1_nav/plan', on_plan, 10)
node.create_subscription(Odometry, '/robot/odom', on_odom, 20)
node.create_subscription(LaserScan, '/robot/scan', on_scan, 5)
last = 0.
while not stop['now'] and time.time() - data['start'] < limit:
    rclpy.spin_once(node, timeout_sec=.05)
    if time.time() - last >= .1:
        p = pose()
        if p is not None:
            last = time.time(); data['poses'].append((round(last - data['start'], 3),) + tuple(round(v, 4) for v in p))
json.dump(data, open(out, 'w'))
print('saved', out, len(data['poses']), 'poses', len(data['plans']), 'plans', len(data['scans']), 'scans',
      'map' if data['map'] else 'NO MAP', flush=True)
