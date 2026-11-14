# Hack the D1

## Slide 1 — Hack the D1

**Opening a closed service robot with ROS 2**

TUWRC track · Building Better Worlds Hackathon 2026

## Slide 2 — The first challenge: getting in

- A USB cable from the Mac to the robot exposed no device or serial port, even after changing cables and ports.
- The built-in Ubuntu screen gave us the first usable terminal.
- A phone's USB tethering gave the robot outbound connectivity.
- A reverse SSH tunnel through our VPS gave us remote shell access.
- We had no sudo access

Speaker note: Direct access from the Mac was unreliable across the tethered network. The robot initiated the tunnel outward, and the Mac connected through the VPS. Tether disconnections caused intermittent tunnel failures.

## Slide 3 — The robot already had a networked brain

**Display computer** Ubuntu 18.04 and ROS 1 Melodic

**Internal controller** ROS master, motor driver and LiDAR on 192.168.0.4

The vendor ROS graph exposed sensor topics, motor control and safety-related services. We could inspect the existing system before sending any motion commands.

Speaker note: The display computer was 192.168.0.2. Vendor source called the controller TX2, though the board identity was not independently verified. No serial device was found on the display computer. The vendor test executable was avoided because it also runs motors and disinfection functions.

## Slide 4 — Bringing the sensors into ROS 2

We ran ROS 2 Humble in a rootless environment on the display computer and built a one-way bridge from the vendor's ROS 1 graph.

- LiDAR, odometry, IMU and rear RGB-D camera delivered data
- Eight air-quality topics delivered messages
- 13 sensor topics passed a live delivery check

Speaker note: The bridge uses an explicit sensor allowlist. Upper and lower depth cameras were registered but did not deliver frames. Air-quality units and calibration remain unverified. Delivery alone does not validate calibration or the full transform tree.

## Slide 5 — Making movement supervised

A drive gate passes ROS 2 velocity commands to the vendor driver. It starts disarmed, limits speed and stops forwarding stale commands.

An independent watchdog requests motor disable and power off when the command stream or safety telemetry fails.

**Physical tests:** supervised floor drives of 0.38 m and 0.98 m, plus in-place turns.

Speaker note: The gate and watchdog share a host and network, so they have common failure points. A person remained at the physical stop. Stand tests preceded floor driving. The red stop remains the primary stop.

## Slide 6 — Mapping and navigation

SLAM Toolbox produced a live map. Nav2 planned toward a named place and controlled the base through the drive gate.

**Completed run:** Nav2 drove 1.04 m to the configured goal in the 08:59:25 bottle demonstration. The session completed successfully and ended with zero speed and motor power off.

**Still open:** navigation to the actual door and the doorbell integration.

Speaker note: The crowded hall affected the demonstration. The robot's laser cannot see behind it, and robot-mounted objects appear in two narrow scan sectors. The navigation setup filters those self-hits and avoids reversing.

## Slide 7 — What we learned

- The vendor's ROS 1 graph was the practical integration point.
- Published interfaces still required live checks: registered cameras did not necessarily deliver frames.
- Motor power and motor enable are separate; the configuration parameter alone did not reflect runtime state.
- A command timeout needs independent supervision: the vendor's own stop after adapter loss was too slow for our intended drive path.

Speaker note: The power RPC also paused safety status updates for around half a second, so watchdog startup needed a separate preparation phase. Laser blind spots and physical supervision remain important limits.

## Slide 8 — Current status and next steps

**Demonstrated** Access, ROS 2 sensor bridge, supervised driving and a completed Nav2 goal.

**Next** Confirm the actual door location, demonstrate that route and integrate the doorbell.

**Doorbell integration** Designed but not implemented; Home Assistant credentials were unavailable.

Speaker note: The 08:59:25 session records command_finished after running d1_goto.py door. That client exits successfully only when Nav2 returns STATUS_SUCCEEDED. The configured place name does not establish arrival at the physical door. Add team names and the final demo before submission.

---

## Evidence and source notes

- Connection attempts and network observations: `docs/d1-connection-check.md`.
- Earlier conversation, 13–14 November: USB attempts, tethering and successful SSH through the VPS reverse tunnel. The tunnel later suffered intermittent disconnects.
- ROS discovery, sensor counts and early stand tests: `docs/findings-log.md` and `docs/evidence/`.
- Latest demonstrated status and architecture: `README.md`, `docs/submission-status.md` and `docs/drive-validation.md`.
- Completed navigation session: `docs/evidence/sessions/20261114T085925-nav2-bottle-film.json`. Success interpretation: `scripts/d1_goto.py` and `scripts/drive-session.py`.
- Candidate visual: `docs/viz/nav2-bottle-run.png`; check that its recorded run and labels match the final narration before using it.
