"""Footprint-aware guards for supervised multi-minute drive sessions.

Pure functions (Python 2 and 3); no ROS imports. Geometry from the live TF
base_link -> front_laser (x=0.197 m) and the 58 x 58 cm body.
"""
import math

LASER_X = .197
HALF = .29          # body half-width/length (58 cm square)
SELF_MARGIN = 0.    # returns inside the body outline are self-hits (housing)
STOP_RADIUS = .46   # rotating square sweeps r=0.41; keep ~5 cm extra
STOP_AHEAD = .33    # distance beyond the front bumper that stops forward travel
SIDE_GAP = .06      # anything closer to the body sides stops all motion
MIN_POINTS = 2      # a single isolated ray is not enough to trip
# Measured self-hits just outside the outline: (angle_from, angle_to, max_range).
# Rays 132-150 (-71..-65 deg) return 0.05-0.33 m with sd < 1 cm over 60 scans and
# stayed fixed while the robot drove 0.38 m (14 Nov): a robot-mounted part at the
# front-right in the laser's field of view.
# Rays 18-36 (-110..-103 deg): rays 30-33 return 0.29-0.31 m (sd < 5 mm) before and
# after turns; while turning the sector reads up to 0.38 m: a loose part (cable?)
# hanging on the right side. Masked to 0.42 m: a 7 degree, ~5 cm blind wedge.
SELF_SECTORS = [(-1.257, -1.126, .36), (-1.930, -1.800, .42)]
# The same bracket protrudes past the bumper while driving: three Nav2 sessions
# (20261114T084805, T084949, T085812) tripped on base_link points x 0.316-0.331,
# y -0.181..-0.235, and earlier sessions show the same patch. Treated as body:
# a 5.5 x 13 cm blind patch at the front-right corner (x <= 0.345, y -0.29..-0.16).
SELF_BOX = (HALF, .345, -.29, -.16)


def _invalid(value, range_min, range_max):
    return (math.isnan(value) or math.isinf(value) or value < range_min or
            value > range_max or abs(value - .002) <= 1e-6)


def scan_points(ranges, angle_min, increment, range_min, range_max):
    """Return (points outside the body, valid count, total count) in base_link."""
    points = []; valid = 0
    for i, r in enumerate(ranges):
        if _invalid(r, range_min, range_max):
            continue
        valid += 1
        a = angle_min + i * increment
        if any(lo <= a <= hi and r <= rmax for lo, hi, rmax in SELF_SECTORS):
            continue
        x = LASER_X + r * math.cos(a); y = r * math.sin(a)
        if abs(x) <= HALF + SELF_MARGIN and abs(y) <= HALF + SELF_MARGIN:
            continue  # self-occlusion (housing, bumper)
        if SELF_BOX[0] < x <= SELF_BOX[1] and SELF_BOX[2] <= y <= SELF_BOX[3]:
            continue  # front-right bracket
        points.append((x, y))
    return points, valid, len(ranges)


def proximity(ranges, angle_min, increment, range_min, range_max, rotating=False,
              forward=True, stop_ahead=STOP_AHEAD):
    """Classify the scan: dict(stop, reason, nearest, coverage, ...).

    Always: anything within SIDE_GAP of the body sides. Forward corridor: unless
    the robot is purely turning in place (forward=False). Swept circle: while
    turning.
    """
    points, valid, total = scan_points(ranges, angle_min, increment, range_min, range_max)
    near = [p for p in points if math.hypot(p[0], p[1]) < STOP_RADIUS]
    ahead = [p for p in points if HALF < p[0] <= HALF + stop_ahead and abs(p[1]) <= HALF + .04]
    side = [p for p in points if abs(p[0]) <= HALF and abs(p[1]) <= HALF + SIDE_GAP]
    nearest = min([math.hypot(*p) for p in points]) if points else None
    coverage = float(valid) / total if total else 0.
    reason = None
    if forward and len(ahead) >= MIN_POINTS: reason = 'obstacle_ahead'
    elif len(side) >= MIN_POINTS: reason = 'obstacle_beside'
    elif rotating and len(near) >= MIN_POINTS: reason = 'obstacle_in_sweep_radius'
    elif coverage < .70: reason = 'scan_coverage'
    closest = sorted(points, key=lambda p: math.hypot(p[0], p[1]))[:3]
    return dict(stop=reason is not None, reason=reason, nearest=nearest, coverage=coverage,
                near=len(near), ahead=len(ahead), side=len(side),
                closest=[(round(p[0], 3), round(p[1], 3)) for p in closest],
                ahead_points=[(round(p[0], 3), round(p[1], 3)) for p in ahead[:5]])


def within_geofence(start, pose, radius):
    return math.hypot(pose[0] - start[0], pose[1] - start[1]) <= radius
