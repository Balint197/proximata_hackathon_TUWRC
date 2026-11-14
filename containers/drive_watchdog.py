"""Independent, latched drive-loss policy. No ROS or hardware operations."""
import math

class DriveWatchdog:
    def __init__(self, idle_timeout=.350):
        self.idle_timeout = idle_timeout
        self.times = {}
        self.pressed = True
        self.power_on = False
        self.prepared = False
        self.prepare_time = None
        self.started = False
        self.ready = False
        self.reason = None
        self.last_motion = None

    def trip(self, reason):
        if self.reason is None:
            self.reason = reason
        self.ready = False

    def _expire(self, now):
        if self.started:
            for name, limit in (('adapter', .150), ('stop', .300), ('power', .300)):
                stamp = self.times.get(name)
                if stamp is None or now < stamp or now - stamp >= limit:
                    self.trip(name + '_stale')

    def gate(self, values, caller, now):
        if caller != '/d1_drive_gate':
            return
        self._expire(now)
        if (len(values) != 6 or not all(math.isfinite(v) for v in values) or
                any(values[i] != 0 for i in (1, 2, 3, 4)) or
                abs(values[0]) > .200001 or abs(values[5]) > .250001):
            self.trip('invalid_adapter_command')
            return
        self.times['adapter'] = now
        if values[0] != 0 or values[5] != 0:
            if not self.started:
                self.trip('motion_before_activation')
            self.last_motion = now

    def stop(self, pressed, now):
        self._expire(now)
        self.times['stop'] = now
        self.pressed = pressed
        if pressed:
            self.trip('physical_stop')

    def power(self, on, now):
        self._expire(now)
        if self.started and self.power_on and not on:
            self.trip('power_lost')
        self.times['power'] = now
        self.power_on = on
        if on and not self.prepared:
            self.trip('power_on_without_ready')

    def _fresh(self, now):
        return all(name in self.times and 0 <= now - self.times[name] < limit
                   for name, limit in (('adapter', .150), ('stop', .300), ('power', .300)))

    def activate(self, requested, now):
        if (not requested or not self.prepared or self.reason is not None or
                not self._fresh(now) or self.pressed or not self.power_on or
                now - self.prepare_time >= 5.):
            self.trip('activation_denied')
        else:
            self.started = True

    def tick(self, now):
        self._expire(now)
        if self.reason is not None:
            return True
        fresh = self._fresh(now)
        if not self.prepared and fresh and not self.pressed and not self.power_on:
            self.prepared = True
            self.prepare_time = now
        if self.prepared and not self.started and now - self.prepare_time >= 5.:
            self.trip('activation_timeout')
        if self.last_motion is not None and now - self.last_motion >= self.idle_timeout:
            self.trip('motion_ended')
        self.ready = self.started and fresh and not self.pressed and self.reason is None
        return self.reason is not None
