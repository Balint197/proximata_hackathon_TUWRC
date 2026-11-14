import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from session_checks import proximity, within_geofence, scan_points

AMIN, INC, N = -2.013, .005817, 693


def scan(default=3.):
    return [default] * N


def put(ranges, deg, r, width=3):
    i = int(round((math.radians(deg) - AMIN) / INC))
    for j in range(i, i + width): ranges[j] = r


class SessionChecks(unittest.TestCase):
    def test_open_room_is_clear(self):
        self.assertFalse(proximity(scan(), AMIN, INC, .05, 23.)['stop'])

    def test_self_hits_inside_body_are_ignored(self):
        r = scan(); put(r, -68, .06, 30)   # observed housing returns
        res = proximity(r, AMIN, INC, .05, 23.)
        self.assertFalse(res['stop']); self.assertEqual(res['near'], 0)

    def test_person_at_bumper_stops(self):
        r = scan(); put(r, 0, .22, 40)      # observed legs ~10 cm past bumper
        res = proximity(r, AMIN, INC, .05, 23.)
        self.assertEqual(res['reason'], 'obstacle_ahead')
        self.assertTrue(res['stop'])

    def test_obstacle_ahead_beyond_sweep_radius_stops(self):
        r = scan(); put(r, 0, .50, 5)       # x = .697 ... beyond radius, within ahead zone? no
        self.assertFalse(proximity(r, AMIN, INC, .05, 23.)['stop'])
        r = scan(); put(r, 0, .40, 5)       # x = .597 -> ahead zone (.29 .. .62)
        res = proximity(r, AMIN, INC, .05, 23.)
        self.assertTrue(res['stop']); self.assertEqual(res['reason'], 'obstacle_ahead')

    def test_side_wall_blocks_turning_but_not_straight_driving(self):
        r = scan(); put(r, -90, .40, 10)    # wall 11 cm right of the body
        self.assertFalse(proximity(r, AMIN, INC, .05, 23.)['stop'])
        self.assertEqual(proximity(r, AMIN, INC, .05, 23., rotating=True)['reason'],
                         'obstacle_in_sweep_radius')

    def test_corridor_ignored_only_for_pure_turns(self):
        r = scan(); put(r, 0, .40, 5)
        self.assertFalse(proximity(r, AMIN, INC, .05, 23., rotating=True, forward=False)['stop'])
        self.assertTrue(proximity(r, AMIN, INC, .05, 23., rotating=True, forward=True)['stop'])

    def test_object_touching_side_always_stops(self):
        r = scan(); put(r, 90, .32, 10)     # 3 cm from the left side
        self.assertEqual(proximity(r, AMIN, INC, .05, 23.)['reason'], 'obstacle_beside')

    def test_measured_front_right_bracket_is_masked(self):
        r = scan()
        for i, v in ((148, .238), (149, .236), (150, .225)): r[i] = v
        self.assertEqual(proximity(r, AMIN, INC, .05, 23.)['ahead'], 0)
        r[149] = r[150] = .40     # a real object further out on the same rays is kept
        self.assertEqual(len(scan_points(r, AMIN, INC, .05, 23.)[0]), N - 1)

    def test_single_ray_does_not_trip(self):
        r = scan(); put(r, 0, .30, 1)
        self.assertFalse(proximity(r, AMIN, INC, .05, 23.)['stop'])

    def test_invalid_rays_reduce_coverage_and_never_count_as_free(self):
        r = [float('nan')] * N
        res = proximity(r, AMIN, INC, .05, 23.)
        self.assertTrue(res['stop']); self.assertEqual(res['reason'], 'scan_coverage')
        r = [.002] * N
        self.assertTrue(proximity(r, AMIN, INC, .05, 23.)['stop'])

    def test_geofence(self):
        self.assertTrue(within_geofence((0, 0, 0), (2., 2., 1), 3.))
        self.assertFalse(within_geofence((0, 0, 0), (3., 1., 1), 3.))


if __name__ == '__main__':
    unittest.main()
