# Hack the D1: an open ROS 2 platform for a closed service robot

TUWRC track, Building Better Worlds Hackathon 2026 (14 November).

The Hyundai D1 is a 74 kg disinfection robot sold as a closed box. This
repository turns it into a ROS 2 robot without flashing, cutting or replacing
anything: we bridge the vendor's own ROS 1 stack into a rootless ROS 2 Humble
environment, add a supervised drive path with an independent watchdog, and run
SLAM Toolbox and Nav2 on top.

## Status by level

| Level | Status | Evidence |
|---|---|---|
| 1. Get in | **Done.** Onboard computers, vendor ROS 1 graph, motor/GPIO services and sensor topics mapped (see below) | [findings log](docs/findings-log.md) |
| 2. Unlock every sensor | **Done for laser, odometry, IMU, rear RGB-D camera, 8 air-quality topics** as ROS 2 topics. Upper/lower depth cameras are registered but never delivered frames | [sensor capture](docs/evidence/ros2-sensors-2026-11-14.jsonl) |
| 3. Take the wheel | **Done.** ROS 2 `/cmd_vel` drives the base on the floor (0.38 m and 0.98 m scripted drives, in-place turns); odometry out; physical stop, command-loss stop and an independent watchdog | [sessions](docs/evidence/sessions/), [drive validation](docs/drive-validation.md) |
| 4. Navigate | **Partial.** Live SLAM map, Nav2 (planner + Regulated Pure Pursuit) driving the real base through the gate, named places (`home`, `door`). Nav2 turned the robot to the goal and drove 0.33 m before people in the busy hall blocked the path; no complete goal reached yet | [nav2 session](docs/evidence/sessions/20261114T073806-nav2-door.json) |
| 5. Answer the door | **Not started** (no Home Assistant credentials available). Design below | |

## What talks to what (level 1)

```
 Display PC (Ubuntu 18.04, 192.168.0.2)            Controller "TX2" (192.168.0.4)
 ├─ 10.1" touch display                           ├─ ROS 1 master :11311
 ├─ USB: 2x Orbbec 2bc5:0401 (upper/lower depth)   ├─ /mot_sbl2360_driver  (motor controller, CAN)
 │        1x 266e:0102                            │    sub /cmd_vel, pub /robot/odom,
 ├─ vendor ROS 1 apps (~/hyundai_ws, ~/catkin_ws)   │    /robot/motor/{actual_vel,encoder,rpm,...}
 └─ THIS REPO: rootless Ubuntu 22.04 + ROS 2       │    srv /robot/motor/enable_srv
      (bubblewrap, host network, no devices)      ├─ /sick_tim571_2050101 -> /robot/scan (front_laser)
                                                  ├─ /imu/imu_node -> /robot/imu/data
                                                  ├─ GPIO: /gpio/motorpower_srv, /robot/motor_power,
                                                  │        /robot/button/emergency_state (red stop)
                                                  ├─ cameras: /camera_back/{rgb,depth}, camera_up/down
                                                  └─ /disinfection/{pm10,pm25,pm100,o3,co2,tvoc,
                                                                    temperature,humidity}
```

Key facts a next team needs:

- The robot is **not** a blank Ubuntu: the vendor ROS 1 Melodic stack runs on
  the controller (`ROS_MASTER_URI=http://192.168.0.4:11311`, `ROS_IP=192.168.0.2`).
  Talking ROS 1 to it is the access path; no serial devices exist on the display PC.
- Motor power is a GPIO relay (`/gpio/motorpower_srv`), then the driver needs
  `/robot/motor/enable_srv`. The `motor_enable` *parameter* does not track runtime
  state; use `/robot/motor/controllable_state` and `/robot/motor_power`.
- The GPIO power RPC blocks for ~0.5 s and pauses stop/power topics meanwhile.
- The base has a turn deadband: angular commands below ~0.05 rad/s do not move it.
- Laser: SICK TiM571, 693 rays, ±115°, 15 Hz, at x = 0.197 m. It **cannot see
  behind** the robot. Rays −71°…−65° and −110°…−103° hit robot-mounted parts
  (bracket front-right, cable on the right side); see `scripts/session_checks.py`.
- Air-quality topics are `std_msgs/Float64`; units/calibration unverified, some read 0.0.
- **Do not run the vendor `d1_test`**: it powers the motors and runs disinfection functions.

More detail, timings and every measurement: [findings log](docs/findings-log.md),
[drive validation](docs/drive-validation.md), [evidence](docs/evidence/).

## Architecture

```
ROS 2 (rootless, domain 42)                       ROS 1 (vendor, on controller)
 d1_goto.py / d1_motion.py / Nav2 ─/cmd_vel─┐
                          /d1/drive_arm ────┤
                                     d1_drive_gate (C++, ROS1+ROS2) ──/cmd_vel──> mot_sbl2360_driver
 sensor bridge <── scan, odom, imu, camera, air quality, tf ───────────────────── vendor nodes
 d1_scan_filter: /robot/scan -> /robot/scan_filtered (self-hits removed) -> Nav2 costmaps
 slam_toolbox: /robot/scan -> /map, map->odom
                                       drive-watchdog.py (ROS 1, independent) ──> enable/power OFF
 drive-session.py (host, ROS 1): preflight, power on, enable, activate watchdog,
                                 run ONE ROS 2 command, monitor guards, power off
```

The sensor bridge is one-way (allowlist, no commands). The only command path
is the drive gate, which starts disarmed, clamps to 0.20 m/s and 0.25 rad/s,
drops to zero 250 ms after the last command, and disarms on stop press or stale
stop status. The watchdog independently disables the motors if the gate's
stream stops, the stop is pressed, or telemetry goes stale.

## Quick start

On the display PC, from this repository:

```bash
bash scripts/setup-rootless-ros2.sh      # once: Ubuntu 22.04 + Humble + ros1_bridge (~GBs)
bash scripts/install-navigation.sh       # once: SLAM Toolbox + Nav2
bash scripts/build-drive-gate.sh         # once: build the drive gate

# long-running, each in its own terminal (or `setsid nohup ... &`):
bash scripts/run-sensor-bridge.sh        # level 2: ROS 1 sensors -> ROS 2
bash scripts/run-mapping.sh              # SLAM: /map and map->odom
bash scripts/run-nav2.sh                 # level 4: Nav2 (cannot move the robot by itself)

bash scripts/ros2-shell.sh               # a ROS 2 shell: source /opt/ros/humble/setup.bash
```

### Driving (level 3): supervised sessions

Every motion runs inside one session. A person keeps a hand on the red stop.

```bash
# scripted, odometry-closed moves (forward only: the laser cannot see behind)
bash scripts/run-session.sh --max-seconds 60 --geofence 2 -- \
    python3 /root/d1-tools/d1_motion.py rotate 90 forward 1.0

# Nav2 to a named place
bash scripts/run-session.sh --max-seconds 150 --geofence 4 -- \
    python3 /root/d1-tools/d1_goto.py door
```

The session (`scripts/drive-session.py`):

1. Preflight: stop released and fresh, motors off, zero velocity, fresh scan and
   odometry, no unexpected `/cmd_vel` publishers.
2. Starts a deadline process that switches motors off at the time limit **or as
   soon as the session process dies**.
3. Starts the gate and watchdog, powers on, enables, activates the watchdog.
4. Runs the ROS 2 command, which arms the gate and streams commands.
5. Ends on: command finished, red stop, watchdog trip, obstacle in the path while
   driving forward, geofence, time limit, stale sensors, or Ctrl-C. Then it kills
   the command sources, disables the motors and switches power off.
6. Writes a JSON record to `docs/evidence/sessions/`.

`--scan-guard full` also stops for anything touching the sides or inside the
turning circle; the default (`forward`) only guards the path ahead, because
cables and an attentive operator near the robot are normal.

### Map and named places (level 4)

```bash
bash scripts/map-snapshot.sh live        # maps/live.{pgm,yaml,png}: map + robot + places
bash scripts/save-place.sh door          # current robot pose -> config/places.yaml
bash scripts/save-place.sh home 0.7 -0.2 1.2   # or explicit map x y yaw
```

To set up the real door: drive or push the robot to the spot in front of the
door (with SLAM running) and run `save-place.sh door`. The map frame is defined
by the running SLAM session; if SLAM is restarted, save the places again.

Nav2 notes (`config/prepare-nav2.py`): Regulated Pure Pursuit instead of DWB
(DWB decayed turns into the base's deadband and stalled), no reversing,
0.15 m/s / 0.20 rad/s, 58 cm square footprint. The global costmap uses live
laser obstacles only, because SLAM kept people's legs in the busy hall as
permanent obstacles that blocked every path.

### Answer the door (level 5): design, not implemented

Home Assistant → (REST API or MQTT) → a small listener on the display PC →
`run-session.sh -- d1_goto.py door`, and the doorbell camera
(`/api/camera_proxy/<camera entity>`) shown full-screen on the D1 display while
it drives. `.env.example` lists the needed settings; credentials belong in an
ignored `.secrets/` file.

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'      # watchdog, floor and session guards
g++ -std=c++14 -Wall -Wextra -Werror -Icontainers tests/test_drive_policy.cpp -o /tmp/p && /tmp/p
bash scripts/test-drive-gate.sh        # gate transport, private ROS 1 master, no hardware
bash scripts/test-drive-watchdog.sh    # watchdog transport with fake motor services
```

## Safety record

- Brief house rules kept: UV-C/plasma untouched, no firmware flashed, nothing
  opened, first drives on a stand, a person on the stop for every motion.
- Every session in `docs/evidence/sessions/` ends with motor power confirmed off.
- Known limits: the watchdog and gate run on the same host and network as
  each other; the laser cannot see behind (the session stops on any reverse
  command); two narrow sectors are masked for robot-mounted parts. The red button
  remains the primary stop.

## Repository map

| Path | What |
|---|---|
| `scripts/run-*.sh` | launchers (bridge, mapping, Nav2, gate, watchdog, session) |
| `scripts/drive-session.py`, `session_checks.py` | supervised session and its scan guard |
| `scripts/d1_motion.py`, `d1_goto.py` | ROS 2 motion primitives and Nav2 goal client |
| `scripts/d1_scan_filter.py` | self-hit filter for Nav2 |
| `containers/` | drive gate (C++), watchdog policy, sensor bridge, DDS profile |
| `config/` | Nav2 parameters and launch, behaviour trees, `places.yaml` |
| `maps/` | saved maps |
| `docs/` | findings log, drive validation, evidence captures |
| `01_recon.sh`, `02_serial_sniffer.py` | early discovery tools (recon output may contain environment data) |
| `03_d1_base_driver.py` | obsolete serial scaffold from before the ROS 1 path was found; do not use |

MIT licensed.

## D1 preparation

- [Track brief](tuwrc-d1-brief.md)
- [USB discovery and software runbook](docs/d1-usb-runbook.md)
- [Hardware research and primary sources](docs/d1-hardware-research.md)
