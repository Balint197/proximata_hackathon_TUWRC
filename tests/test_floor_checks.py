import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from floor_checks import front_clearance, pose_within_limit
class FloorChecks(unittest.TestCase):
    def test_front_sector_ignores_side_obstacles(self):
        r=[.1]+[1.]*39+[.1]
        result=front_clearance(r,-1.,.05,.05,23.)
        self.assertTrue(result['clear']); self.assertEqual(result['minimum'],1.)
    def test_near_obstacle_and_unknown_ranges_refuse_motion(self):
        self.assertFalse(front_clearance([.29]*20,-.2,.02,.05,23.)['clear'])
        for value in (float('nan'),float('inf'),0.,24.):
            self.assertFalse(front_clearance([value]*20,-.2,.02,.05,23.)['clear'])
    def test_mixed_unknown_or_below_minimum_sector_refuses_motion(self):
        for bad in (float('nan'),0.,.01):
            ranges=[1.]*41; ranges[20]=bad
            self.assertFalse(front_clearance(ranges,-1.,.05,.05,23.)['clear'])
        ranges=[1.]*401; ranges[195:205]=[float('inf')]*10
        self.assertFalse(front_clearance(ranges,-1.,.005,.05,23.)['clear'])
        self.assertFalse(front_clearance([1.]*20,-.2,.02,.05,23.)['clear'])

    def test_isolated_infinite_rays_need_95_percent_finite_coverage(self):
        ranges=[1.]*401; ranges[200]=float('inf')
        self.assertTrue(front_clearance(ranges,-1.,.005,.05,23.)['clear'])
        ranges[201]=float('inf'); ranges[202]=float('inf')
        self.assertFalse(front_clearance(ranges,-1.,.005,.05,23.)['clear'])

    def test_two_isolated_missing_returns_in_real_scan_resolution(self):
        ranges=[1.]*693
        ranges[340]=float('inf'); ranges[350]=float('inf')
        self.assertTrue(front_clearance(ranges,-2.013,.005817,.05,23.)['clear'])
        ranges=[1.]*41; ranges[20]=float('inf')
        self.assertFalse(front_clearance(ranges,-1.,.05,.05,23.)['clear'])

    def test_small_adjacent_missing_pair_is_bounded_by_angle_and_coverage(self):
        ranges=[1.]*693; ranges[340:342]=[float('inf')]*2
        self.assertTrue(front_clearance(ranges,-2.013,.005817,.05,23.)['clear'])
        ranges[342]=float('inf')
        self.assertFalse(front_clearance(ranges,-2.013,.005817,.05,23.)['clear'])

    def test_too_few_valid_rays_refuse_motion(self):
        self.assertFalse(front_clearance([1.]*3,-.1,.1,.05,23.)['clear'])
    def test_pose_guard_handles_yaw_wrap_and_limits(self):
        self.assertTrue(pose_within_limit((0,0,math.pi-.01),(.04,0,-math.pi+.01)))
        self.assertFalse(pose_within_limit((0,0,0),(.16,0,0)))
        self.assertFalse(pose_within_limit((0,0,0),(0,0,.31)))
if __name__=='__main__': unittest.main()

class QualityTimingTests(unittest.TestCase):
    def test_near_obstacle_stops_immediately_but_minor_missing_burst_recovers(self):
        from floor_checks import ScanQualityGuard
        guard=ScanQualityGuard()
        good=dict(clear=True,minimum=1.2,valid=180,total=180,hard_stop=False,missing_only=True)
        small_gap=dict(clear=False,minimum=1.2,valid=177,total=180,hard_stop=False,missing_only=True)
        self.assertFalse(guard.stop(good,1))
        self.assertFalse(guard.stop(small_gap,1.1))
        self.assertFalse(guard.stop(good,1.17))
        self.assertFalse(guard.stop(small_gap,1.2))
        self.assertTrue(guard.stop(small_gap,1.401))
        self.assertTrue(ScanQualityGuard().stop(dict(good,minimum=.3),1))
        self.assertTrue(ScanQualityGuard().stop(dict(good,hard_stop=True),1))
    def test_large_unknown_sector_stops_immediately(self):
        from floor_checks import ScanQualityGuard
        self.assertTrue(ScanQualityGuard().stop(dict(clear=False,minimum=1.,valid=10,total=180,hard_stop=False,missing_only=True),1))

class ComposedQualityTests(unittest.TestCase):
    def test_nan_out_of_range_and_bad_coverage_never_receive_grace(self):
        from floor_checks import ScanQualityGuard
        for invalid in (float('nan'),24.,-.1):
            ranges=[1.]*693; ranges[340]=invalid
            result=front_clearance(ranges,-2.013,.005817,.05,23.,.5)
            self.assertTrue(ScanQualityGuard().stop(result,1))
        result=front_clearance([1.]*20,-.2,.02,.05,23.,.5)
        self.assertTrue(ScanQualityGuard().stop(result,1))

class SickReservedValueTests(unittest.TestCase):
    def test_code_two_is_missing_not_two_mm_obstacle_and_needs_clear_neighbors(self):
        from floor_checks import ScanQualityGuard
        ranges=[1.2]*693
        ranges[262]=.002
        for i in (339,361,396): ranges[i]=float('inf')
        result=front_clearance(ranges,-2.013,.005817,.05,23.,.5)
        self.assertTrue(result['clear']); self.assertFalse(result['hard_stop'])
        self.assertFalse(ScanQualityGuard().stop(result,1))
        ranges[263]=.2
        self.assertTrue(ScanQualityGuard().stop(front_clearance(ranges,-2.013,.005817,.05,23.,.5),1))
    def test_many_reserved_values_or_other_below_min_values_do_not_clear(self):
        ranges=[1.2]*693; ranges[300:320]=[.002]*20
        self.assertFalse(front_clearance(ranges,-2.013,.005817,.05,23.)['clear'])
        ranges=[1.2]*693; ranges[340]=.01
        self.assertTrue(front_clearance(ranges,-2.013,.005817,.05,23.)['hard_stop'])
