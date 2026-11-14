import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from stand_startup import safe_to_enable, stop_motion_sources
class StartupTests(unittest.TestCase):
    def test_post_rpc_requires_live_untripped_supervision_and_fresh_stop(self):
        good = dict(button=False, button_time=1., watchdog_time=1.,
                    watchdog_prepared=True, watchdog_tripped=False, power=True)
        self.assertTrue(safe_to_enable(good, 1.01, False, True))
        for change in (dict(button=True), dict(button_time=.5),
                       dict(watchdog_time=.5), dict(watchdog_prepared=False),
                       dict(watchdog_tripped=True), dict(power=False)):
            state = dict(good); state.update(change)
            self.assertFalse(safe_to_enable(state, 1.01, False, True), change)
        self.assertFalse(safe_to_enable(good, 1.01, True, True))
        self.assertFalse(safe_to_enable(good, 1.01, False, False))
    def test_sources_stop_and_watchdog_trips_before_service_cleanup(self):
        events=[]
        class Child:
            def __init__(self,name): self.name=name
            def poll(self): return None
        stop_motion_sources(Child('stimulus'),Child('gate'),
                            lambda: events.append('trip'),
                            lambda child: events.append('kill_'+child.name))
        events.append('services')
        self.assertEqual(events,['kill_stimulus','trip','kill_gate','services'])
    def test_failed_trip_request_still_stops_gate_and_allows_cleanup(self):
        events=[]
        class Child:
            def poll(self): return None
        def failed_trip(): raise RuntimeError('ROS disconnected')
        result=stop_motion_sources(None,Child(),failed_trip,lambda c: events.append('kill'))
        events.append('services')
        self.assertFalse(result); self.assertEqual(events,['kill','services'])
if __name__ == '__main__': unittest.main()
