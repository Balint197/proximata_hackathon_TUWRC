# Drive validation before ROS 2 control

The sensor bridge remains one-way. No ROS 2 command route is enabled.

## Passive baseline — 14 November 2026

The live vendor driver reports motor enable false. A five-second read-only
sample received 497 actual-velocity messages, all zero, and 50 emergency
button messages, all false. Two zero `/cmd_vel` messages arrived despite no
test command publisher. The vendor driver both publishes and subscribes to
`/cmd_vel`; command-loss testing must account for this behavior.

Evidence: [passive baseline](evidence/passive-stop-baseline-2026-11-14.json).
Neither physical stop operation nor a command-loss watchdog is verified.
In a subsequent operator-confirmed button test, 450 messages arrived over
45 seconds: false initially, true at 0.594 seconds, and false at 7.087 seconds.
Motor enable remained false. This establishes the reported signal polarity
(pressed = true), but does not verify stopping during motion. See the
[repeat capture](evidence/physical-stop-signal-repeat-2026-11-14.json).
No watchdog timeout was exposed in the inspected motor-driver parameters;
this does not establish that the driver has no watchdog.

## Stand power diagnostic

The first 0.08 rad/s command test accepted motor enable but reported zero
wheel velocity. A subsequent check found `/robot/motor_power` false.
For an isolated comparison, the vendor `/gpio/motorpower_srv` was set true
before repeating the same command. Actual angular velocity then reached
0.194 rad/s. This supports missing motor power as a cause of the earlier
nonmovement; it does not establish a low-speed deadband. Actual speed also
exceeded the request, so commanded speed is not a verified physical bound.
No stop-button transition occurred during the six-second test. Cleanup
confirmed motor enable false, motor power false, and zero velocity.
The physical stop under motion and command-loss watchdog remain unverified.
See [diagnostic evidence](evidence/stand-power-diagnostic-2026-11-14.json).

The operator subsequently reported pressing the red stop about two seconds
after motion began and seeing the wheels stop immediately. Detailed review
supports an early stop: motion first appeared at t=2.562 s, feedback was
near zero in t=5–6 s and zero throughout t=6–8 s, while commands continued
until t=8.176 s. A small feedback transient occurred at t=9.042 s during
power-off cleanup. No emergency-topic transition was logged during that
run. Record the operator observation separately from telemetry: the cause
of the early stop and the missing emergency transition remain unresolved.
Do not interpret the timed command ending as the time the wheels stopped.
A subsequent passive capture received 450 emergency messages and recorded
pressed=true at t=12.937 s, released=false at t=20.233 s. Motor power stayed
false and motor enable remained false. The same button signal can therefore
be observed, but the missing transition during motion is still unexplained.
See [reconciliation capture](evidence/stop-reconciliation-2026-11-14.json).

## Synchronized repeat: speed guard triggered

The repeat held the request at 0.08 rad/s. Both observed `/cmd_vel` and
`/filtered_cmd_vel` peaked at approximately 0.08 rad/s, while
`/robot/motor/actual_vel` peaked at 0.3295 rad/s (with linear x 0.0919 m/s
in the same sample). The 0.25 feedback-speed guard ended commands at
t=9.262 s, about 2.04 seconds after the motion command began. Power-off
was confirmed at t=10.012 s; the operator's stop press was captured at
t=10.113 s and release at t=12.513 s. Final enable and power were false,
and final velocity zero. The stop press therefore cannot be credited with
triggering this test's stop. Do not increase the command or relax the guard.

Next investigate feedback scaling/quantization, wheel regulation, and the
vendor driver's control behavior before another powered test. The evidence
locates the mismatch downstream of the filtered command, but does not
establish whether the discrepancy is physical speed or reported speed.
Physical stop under motion and watchdog behavior remain unverified.
See [synchronized evidence](evidence/synchronized-stop-repeat-2026-11-14.json).

## Read-only analysis of speed feedback

The 0.3295 rad/s peak occurred in two consecutive messages about 9 ms apart.
Across the 2.038-second command interval, time-integrated feedback averaged
0.04785 rad/s, below the 0.08 request. The earlier description of a fourfold
speed mismatch referred to a brief peak, not sustained motion.

All angular samples match multiples of 0.0193815 rad/s, the kinematic step
predicted for one RPM of wheel-speed difference using radius 0.065 m and
track 0.3512 m. This is consistent with quantized RPM-derived feedback.
It does not establish whether the peak is physical overshoot or a reporting
artifact. Simultaneous raw encoder/RPM capture during motion is needed to
distinguish them; neither was recorded in the preceding motion runs.

A five-second passive capture verified both raw channels deliver roughly
100 messages/s. RPM remained zero and encoder counts remained fixed at
left=-832, right=738; motor enable and power were false. The vendor driver
implementation was not found locally; generated message/config bindings
and launch references exist in `~/clobot_ws`.

Evidence: [offline analysis](evidence/speed-feedback-analysis-2026-11-14.json),
[passive encoder/RPM capture](evidence/passive-rpm-encoder-2026-11-14.json).
Next powered diagnostic should capture raw encoders, actual RPM, requested
RPM, actual velocity, commands, and button state together, retaining the
existing speed guard and bounded stand-test duration.

## Raw-channel stand test

The next bounded test ended on the physical stop signal, 2.494 seconds
after commands began. The button changed true at t=9.744854 s and motor
power changed false at t=9.744952 s; software ended commands at t=9.758237 s.
These are host receipt times, not instrumented electrical latency. Power
dropped before the test's explicit zero/disable/power-off cleanup, providing
evidence that the vendor stop path operates independently of that cleanup.
The cleanup power-off service returned an error after power was already
reported false. Final power and enable were false; final velocity was zero.

Actual velocity exactly matched kinematics computed from the nearest actual
RPM sample throughout the capture (1281 velocity samples). Requested wheel
RPM was left -2 to 0, right 0 to 2. Actual RPM ranged left -5 to +9 and
right -4 to +8. Angular feedback peaked in magnitude at 0.1744 rad/s and
included direction reversals. Encoder counts changed too, so quantization
alone is not an established explanation for all variation. Gearing, encoder
scale, sign conventions, unloaded regulation, and external wheel handling
have not been independently calibrated.

Small nonzero feedback persisted intermittently after the press, with the
last nonzero sample at t=12.178853 s (angular -0.01938 rad/s). Therefore this
capture does not establish instantaneous physical standstill or a certified
stopping time. Do not use the 13 ms software response as physical stop time.
No command-loss watchdog test has been performed.

Evidence: [raw capture](evidence/raw-drive-diagnostic-2026-11-14.json),
[analysis](evidence/raw-drive-analysis-2026-11-14.json).

## Next checks, in order

1. Confirm wheels off the ground, disinfection hardware disconnected, and a
   person with a hand on the stop, as required by the track brief.
2. Keep motor enable false. Observe `/robot/button/emergency_state` while
   the operator presses and releases the physical stop. Record both states
   and timestamps. Software telemetry alone does not prove physical stopping.
3. On the stand, use a brief low-speed rotation while the operator activates
   the physical stop. Record requested and actual velocity, emergency state,
   and enable state. Send zero and disable on every exit. Do not automatically
   re-enable after a stop or after releasing it.
4. Test command loss separately, with an independent time-bounded cleanup
   path that sends zero and disables the motors. Record all `/cmd_vel`
   publishers and messages so vendor self-publication cannot be mistaken for
   loss of commands. If feedback does not stop promptly, abort the test and
   record the watchdog as unverified or failed, according to the evidence.
5. Define the ROS 2 drive gate only after these results: bounded speed,
   freshness timeout, explicit enable, stop latching, and no automatic resume.
   Verify it on the stand before floor driving. Autonomous runs need a mentor.

Passing a software gate test does not replace testing the physical stop.

## ROS 2 stand command-loss test

The ROS 2 gate was built and its isolated transport tests passed before this
supervised stand test. Initial attempts aborted before commands: an immediate
configuration-parameter enable check failed, then a stale ROS registration
blocked the publisher preflight. Targeted cleanup removed only the dead
`/d1_drive_gate` registration. Clean shutdown now requests ROS node shutdown
before terminating its wrapper.

The vendor `motor_enable` configuration parameter remains false even when
`/robot/motor/enable_srv` returns true. A later test recorded the live
`/robot/motor/controllable_state` message: `ui_srv_call` and `result` became
true during enable. The configuration parameter alone must therefore not be
used as proof of runtime motor disable. Power telemetry, live controllable
status and actual feedback must also be checked.

An intervening attempt lost connectivity before commands. NetworkManager
showed enp1s0 disconnected by user/client with no 192.168.0.2 address. The
pending test process was terminated before restoring the existing
`netplan-enp1s0` profile. Only disable/power-off calls and passive checks were
performed immediately after restoration.

The completed test sent ROS 2 angular commands of 0.08 rad/s for about 1.5 s.
The gate's ROS 1 nonzero output interval was 1.740 s, consistent with the
250 ms command timeout. ROS 2 armed status latched false after stream loss.
Actual angular velocity peaked at 0.1744 rad/s. No physical stop press was
recorded during this run. A separate deadline process only sends zero and
disables; it never enables anything.

**Physical stopping remains unresolved.** After the final nonzero command,
small nonzero feedback persisted intermittently for 4.096 s. In the interval
starting 200 ms after zero output and ending before disable, 69 of 302
velocity samples were nonzero (peak linear 0.00681 m/s, angular 0.05814 rad/s).
Encoders changed by left -26 / right +30 counts in that interval. This is
not proof of prompt standstill. Final power false and final velocity zero
were verified. No floor drive, gate-process-death watchdog test or Nav2
motion has been performed.

Evidence: [ROS 2 stand capture](evidence/ros2-stand-command-loss-2026-11-14.json),
[stimulus events](evidence/ros2-stand-stimulus-2026-11-14.jsonl),
[analysis](evidence/ros2-stand-analysis-2026-11-14.json).
The scripts `stand-ros2-test.py` and `stand-ros2-command.py` reproduce only
this supervised stand diagnostic; the host supervisor requires ROS Melodic
and the vendor message PYTHONPATH. They are not an unattended drive launcher.
Next establish whether visible creeping matches the feedback and implement
an independent disable-on-fault supervisor before considering floor motion.

A later passive post-test check still showed power false, ui_srv_call false,
result false and zero velocity, but no_error was false. Motor parameter flags
showed the previously observed undervoltage flag true and other listed fault
flags false. The relationship between that parameter and the live error
status is unverified. Do not clear faults or resume motion without diagnosing
it; [captured flags](evidence/post-stand-motor-flags-2026-11-14.json).

## Operator observation and passive fault follow-up

The operator reported that the wheels stopped quickly in the ROS 2 stream-loss
test. This is a useful visual observation, separate from the intermittent
nonzero telemetry; no instrumented physical stopping time is claimed.

The passive follow-up reported battery voltage 25.5, percentage 47 and
temperature 25 (topic units/calibration not independently verified). The
error message was `GPIO: Motor Power Disable`, cause `Motor Power OFF`,
level WARN, matching the deliberate off state. The configuration undervoltage
flag remains true; its freshness and relation to the live error status remain
unverified. No fault was cleared. See
[passive capture](evidence/passive-fault-check-2026-11-14.json).

## Adapter process-loss stand test

With the same bounded command and physical supervision, the adapter process
was deliberately killed 0.7 s after the stimulus began. The ROS 1 capture now
records publisher caller IDs. No further adapter commands arrived after the
kill. The vendor driver published zero 1.264 s later, before the test
supervisor's explicit zero/disable cleanup at about 2.0 s after the kill.
In the interval 300–1000 ms after adapter loss, all 70 velocity feedback
samples were nonzero, peaking at angular magnitude 0.1163 rad/s. No stop-button
press was recorded in this run.

This does **not** demonstrate a prompt fail-closed stop on process death.
Vendor self-publication remains part of the observed chain, so this cannot
isolate a low-level controller watchdog. Final power was false and final
velocity zero. The deliberately killed node's stale ROS registrations were
removed only after its endpoint was confirmed unreachable.

Before floor/Nav2 use, add a separate supervisor that monitors adapter output
freshness independently, disables motors on loss, latches the failure, and
never enables power or automatically rearms. Its behavior must then be
verified on the stand. Existing in-process timeout alone is insufficient.

Evidence: [process-loss capture](evidence/ros2-stand-gate-loss-2026-11-14.json),
[analysis](evidence/ros2-stand-gate-loss-analysis-2026-11-14.json).
Reproducer: `stand-ros2-test.py --run --gate-loss`, with the same physical
stand/stop supervision and ROS 1 environment required by the previous test.

## Independent watchdog implementation and stand validation

Added a separate ROS 1 watchdog, pure policy tests and isolated transport
tests. The first stand attempt tripped before motion because the GPIO power
RPC paused emergency/power messages for about 0.51 s. The startup sequence
now prepares with power off and zero commands, permits a maximum five-second
power initialization window, then requires explicit activation with fresh
safe status and power on. Nonzero commands during preparation trip. Active
150 ms adapter and 300 ms status deadlines are unchanged. Post-activation
power loss latches too. A post-power-RPC admission check prevents an enable
request after a stop, timeout, supervisor failure or stale telemetry.

In the subsequent stand run, adapter loss was detected after 158.98 ms;
supervisor zero publication arrived at 159.24 ms. The live motor
`ui_srv_call` became false at 193.03 ms, before the harness cleanup-disable
call at 678.38 ms. Thus independent disable is evidenced before the harness
cleanup. Power false was received at 763.34 ms; this overlaps cleanup and
must not be described as an isolated supervisor power-off latency.

The harness ended on stale feedback/status during the blocking GPIO-off RPC,
rather than its planned power-off observation branch. Final power false and
zero velocity were confirmed. No electrical latency or physical stop time is
claimed. A closed-topic exception on orderly watchdog shutdown was then
reproduced with fake services and fixed using a pre-close ROS shutdown hook;
no additional powered test was needed for that lifecycle-only correction.

Evidence: [stand capture](evidence/ros2-stand-watchdog-2026-11-14.json),
[analysis](evidence/ros2-stand-watchdog-analysis-2026-11-14.json),
[isolated tests](evidence/drive-watchdog-isolated-2026-11-14.json).

Remaining: validate floor odometry and geometry at bounded speed under mentor
supervision, configure Nav2/localization/door goal, and integrate Home
Assistant when credentials/entity names arrive. The watchdog is not a
hardware safety controller and does not cover its own process or host loss.
