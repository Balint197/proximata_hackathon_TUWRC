# Independent drive watchdog

Direction authorized by the user's instruction to continue after the process-loss finding.
Use a separate ROS 1 process, independent of the dual-ROS adapter. Observe
/cmd_vel only when callerid is /d1_drive_gate; vendor publications must not
refresh its timer. Observe emergency status and motor-power telemetry.

Adapter freshness: 150 ms. Emergency/power freshness: 300 ms. Once nonzero
commands have occurred, 350 ms of zero commands trips the supervisor. Commands
must be finite, planar and within the adapter limits (0.10 m/s, 0.08 rad/s).
Startup readiness requires fresh released emergency status, adapter output
and power telemetry. Power-on without readiness trips. Once ready, stale
inputs or pressed stop latch a trip, even if motor power is already off.
Recovery requires explicit process restart while power is off; no automatic
rearm and no power-enable calls.

On hardware-mode trip, publish zero at 50 Hz and independently call both
vendor SetBool services with false. Retry each at most once per second,
without allowing a stuck service call to block the monitoring loop or the
other disable service. Default mode is dry-run: no command publisher or
service calls. Publish ready/tripped status for the stand-test harness.

Alternatives: an in-process timeout cannot survive adapter death (observed);
relying solely on vendor self-publication left over a second of command-loss
latency (observed). Separate ROS 1 supervision is the chosen next step.
It still shares host/controller/network failure modes and is not a hardware
safety controller. Validate offline and on the stand before floor motion.

## Startup refinement from the stand capture
GPIO motor-power RPCs block stop/power publication for about 0.5 s. Startup is
two-phase: prepare only after fresh safe inputs with power off; report prepared,
not ready. Preparation permits only zero commands and expires after 5 s.
The operator/test sequence powers on while the adapter remains disarmed, waits
for fresh telemetry, then explicitly publishes true to
/d1/drive_supervisor_activate. Activation requires prepared state, fresh inputs,
released stop and power on. Only then report ready and enforce all runtime
freshness deadlines. Stop press or nonzero commands before activation trip.
After activation, power loss latches a trip too. Restart while already powered
on still trips. No timeout limits are increased during active supervision.
