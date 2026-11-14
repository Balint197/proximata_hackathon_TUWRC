import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'containers'))
from drive_watchdog import DriveWatchdog

class WatchdogTests(unittest.TestCase):
    def ready(self):
        p = DriveWatchdog()
        p.power(False, 1); p.stop(False, 1)
        p.gate([0]*6, '/d1_drive_gate', 1)
        self.assertFalse(p.tick(1)); self.assertTrue(p.prepared); self.assertFalse(p.ready)
        p.power(True, 1.01); p.activate(True, 1.01)
        self.assertFalse(p.tick(1.01)); self.assertTrue(p.ready)
        return p

    def test_startup_requires_all_inputs(self):
        p = DriveWatchdog()
        self.assertFalse(p.tick(0)); self.assertFalse(p.ready)
        p.power(True, 1)
        self.assertTrue(p.tick(1)); self.assertEqual(p.reason, 'power_on_without_ready')

    def test_restart_while_power_on_trips_even_with_fresh_inputs(self):
        p = DriveWatchdog(); p.power(True, 1); p.stop(False, 1)
        p.gate([0]*6, '/d1_drive_gate', 1)
        self.assertTrue(p.tick(1))

    def test_power_transition_waits_for_explicit_activation(self):
        p = DriveWatchdog(); p.power(False, 1); p.stop(False, 1)
        p.gate([0]*6, '/d1_drive_gate', 1); p.tick(1)
        p.power(True, 1.6); p.gate([0]*6, '/d1_drive_gate', 1.6)
        self.assertFalse(p.tick(1.6)); self.assertFalse(p.ready)
        p.stop(False, 1.61); p.activate(True, 1.61)
        self.assertFalse(p.tick(1.61)); self.assertTrue(p.ready)

    def test_preparation_cannot_allow_motion_or_wait_forever(self):
        for move in (True, False):
            p = DriveWatchdog(); p.power(False, 1); p.stop(False, 1)
            p.gate([0]*6, '/d1_drive_gate', 1); p.tick(1)
            if move: p.gate([0,0,0,0,0,.08], '/d1_drive_gate', 1.1)
            self.assertTrue(p.tick(1.1 if move else 6.01))

    def test_vendor_messages_do_not_refresh_adapter(self):
        p = self.ready()
        p.gate([0]*6, '/mot_sbl2360_driver', 1.14)
        self.assertTrue(p.tick(1.151)); self.assertEqual(p.reason, 'adapter_stale')

    def test_callback_after_gap_cannot_revive(self):
        p = self.ready(); p.gate([0]*6, '/d1_drive_gate', 1.16)
        self.assertTrue(p.tick(1.16))

    def test_release_and_recovery_do_not_rearm(self):
        p = self.ready(); p.stop(True, 1.01)
        p.stop(False, 1.02); p.gate([0]*6, '/d1_drive_gate', 1.02)
        self.assertTrue(p.tick(1.02)); self.assertFalse(p.ready)

    def test_stale_status_trips_despite_live_gate(self):
        for stale in ('stop', 'power'):
            p = self.ready()
            for now in (1.1, 1.2, 1.31):
                p.gate([0]*6, '/d1_drive_gate', now)
                getattr(p, 'power' if stale == 'stop' else 'stop')(stale == 'stop', now)
            self.assertTrue(p.tick(1.31)); self.assertEqual(p.reason, stale+'_stale')

    def test_zero_commands_after_motion_disable(self):
        p = self.ready(); p.gate([0,0,0,0,0,.08], '/d1_drive_gate', 1.01)
        for now in (1.1, 1.2, 1.3, 1.37):
            p.stop(False, now); p.power(True, now)
            p.gate([0]*6, '/d1_drive_gate', now); p.tick(now)
        self.assertTrue(p.tick(1.37)); self.assertEqual(p.reason, 'motion_ended')

    def test_configured_idle_timeout_allows_short_pause_then_latches(self):
        p = DriveWatchdog(1.5)
        p.power(False, 1); p.stop(False, 1); p.gate([0]*6, '/d1_drive_gate', 1); p.tick(1)
        p.power(True, 1.01); p.activate(True, 1.01)
        p.gate([.05,0,0,0,0,0], '/d1_drive_gate', 1.02)
        now = 1.02
        while now < 2.4:
            now += .1
            p.stop(False, now); p.power(True, now); p.gate([0]*6, '/d1_drive_gate', now)
            self.assertFalse(p.tick(now))
        p.gate([.05,0,0,0,0,0], '/d1_drive_gate', now)   # resumes before 1.5 s idle
        while now < 4.1:
            now += .1
            p.stop(False, now); p.power(True, now); p.gate([0]*6, '/d1_drive_gate', now)
            p.tick(now)
        self.assertEqual(p.reason, 'motion_ended')

    def test_idle_zeros_before_motion_remain_ready(self):
        p = self.ready()
        for now in (1.1, 1.2, 1.3, 1.4, 1.5):
            p.stop(False, now); p.power(True, now)
            p.gate([0]*6, '/d1_drive_gate', now)
            self.assertFalse(p.tick(now))
        self.assertTrue(p.ready)

    def test_power_loss_after_activation_latches(self):
        p = self.ready(); p.power(False, 1.02); p.power(True, 1.03)
        self.assertTrue(p.tick(1.03)); self.assertEqual(p.reason, 'power_lost')

    def test_invalid_adapter_commands_trip(self):
        for values in ([float('nan'),0,0,0,0,0], [0,1,0,0,0,0], [.21,0,0,0,0,0], [0,0,0,0,0,.26]):
            p = self.ready(); p.gate(values, '/d1_drive_gate', 1.01)
            self.assertTrue(p.tick(1.01)); self.assertEqual(p.reason, 'invalid_adapter_command')

if __name__ == '__main__': unittest.main()
