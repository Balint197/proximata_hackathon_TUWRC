# D1 findings log (chronological, 14 November 2026)

Detailed record kept from the first half of the hackathon. The current overview
and how-to live in the top-level [README](../README.md). Relative links below
have been adjusted for this location.

TUWRC, Building Better Worlds Hackathon 2026.

## Verified onboard findings

Read-only inspection on 14 November 2026 found an existing, running vendor
ROS 1 stack. The robot is not a blank Ubuntu installation.

- Display computer: Ubuntu 18.04.6, kernel 5.4.0-84, ROS Melodic in
  `/opt/ros/melodic`, Ethernet address `192.168.0.2/24`.
- Vendor launch script `/home/hrc/hyundai_ws/src/d1_test/scripts/d1_test.sh`
  specifies `ROS_MASTER_URI=http://192.168.0.4:11311` and
  `ROS_IP=192.168.0.2`.
- Motor and LiDAR node XML-RPC endpoints are on `192.168.0.4`.
  Vendor source refers to this controller as TX2; its board identity has not
  been independently checked.
- USB enumeration returned two `2bc5:0401` devices and one `266e:0102`
  device. Installed software includes Astra/OpenNI/Orbbec drivers. Device
  models and their physical camera positions still need verification.
- No `/dev/ttyUSB*`, `/dev/ttyACM*`, `/dev/video*`, or serial by-id/by-path
  entries were present on the display computer during inspection.

| Interface | Evidence | Status |
|---|---|---|
| `/robot/scan` | `/sick_tim571_2050101`, `sensor_msgs/LaserScan`, frame `front_laser` | Received one header; range quality/rate unmeasured |
| `/robot/odom` | `/mot_sbl2360_driver`, `nav_msgs/Odometry`, `odom` → `base_link` | Received one full message with zero reported velocity |
| `/robot/button/emergency_state` | `std_msgs/Bool`, motor driver subscribes | Received `False`; polarity and physical stopping behavior unverified |
| `/disinfection/co2` | Registered air-quality topic | Received `0.0`; validity and calibration unverified |
| `/camera_up/depth/image_raw`, `/camera_down/depth/image_raw` | Live ROS graph and vendor test source | Registered; image delivery unverified |
| `/camera_back/rgb/image_raw`, `/camera_back/depth/points` | Live ROS graph | Registered; image/cloud delivery unverified |
| `/robot/imu/data` | `/imu/imu_node` registered | Delivery unverified |
| `/robot/motor/encoder`, `/robot/motor/actual_vel` | Motor driver publications | Delivery and units unverified |
| `/disinfection/{pm10,pm25,pm100,o3,tvoc,temperature,humidity}` | Live ROS graph | Registered; readings unverified |
| `/cmd_vel` | Motor driver subscribes **and publishes** | No commands sent; feedback/filtering semantics unverified |
| `/filtered_cmd_vel` | Motor driver publishes | Semantics unverified |

The graph also exposes motor power/enable services, LED services, battery
telemetry, cliff detection, and Chameleon navigation services. Registration
alone does not prove an interface works. No motion, power-enable, disinfection,
or navigation service was invoked during discovery.

## Reproduce read-only inspection

Run on the display computer with network access to the controller:

```bash
source /opt/ros/melodic/setup.bash
export ROS_MASTER_URI=http://192.168.0.4:11311
export ROS_IP=192.168.0.2
rosnode list
rostopic list
rosservice list
rosnode info /mot_sbl2360_driver
timeout 5 rostopic echo -n 1 /robot/odom
timeout 5 rostopic echo -n 1 /robot/scan/header
```

The Codex sandbox blocks hardware/network discovery; these checks required
approved execution outside it. An empty sandbox process list is not evidence
that the vendor stack is stopped.

## Repository tools and limitations

- `01_recon.sh`: system discovery archive. It includes environment variables
  and process command lines; inspect and redact captures before sharing.
- `02_serial_sniffer.py`: serial scanning, JSONL capture comparison, and raw
  packet transmission; requires Python 3 and `pyserial`. No local serial
  controller was found, so do not assume this is the correct access path.
- `03_d1_base_driver.py`: **unverified ROS 2 scaffold**, requiring `rclpy`,
  ROS message packages, `tf2_ros`, and `pyserial`. Its AA55 packet format is
  invented example data, wheel geometry is assumed, and its odometry is
  integrated commanded motion, not decoded feedback. Keep `dry_run=true`.
  Do not connect this scaffold to real hardware.

Vendor test source lives in `/home/hrc/hyundai_ws/src/d1_test/`; installed
navigation configuration is in
`/home/hrc/catkin_ws/install/share/chameleon_config/`. Read these as references.
**Do not run `d1_test`: it enables motor power, drives wheels, and exercises
disinfection functions.**

## Remaining work

### Local ROS 2 environment (rootless)

The robot has Bubblewrap and working unprivileged user namespaces, so Docker
and a sudo password are unnecessary. Ubuntu 22.04 lives under
`~/.local/share/d1-ros2/rootfs`; all installed packages stay in that tree.
The launcher shares the host network, creates private process/IPC namespaces,
and exposes no host hardware devices. Namespace root maps to the invoking
host user, not host root.

Setup and build (downloads hundreds of MB and uses a few GB of disk;
allow time for compilation):

```bash
bash scripts/setup-rootless-ros2.sh
```

This uses official ROS 2 Humble packages and community-maintained ROS One
packages from `https://ros.packages.techfak.net` for the ROS 1 side. The
upstream bridge source is pinned in the setup script. Its example
`static_bridge` executable is replaced with `containers/d1_sensor_bridge.cpp`:
an explicit, one-way sensor allowlist. No commands or services are bridged.
Upper/lower cameras remain excluded pending confirmed delivery.

Run the bridge in one terminal; Ctrl-C stops it:

```bash
bash scripts/run-sensor-bridge.sh
```

Verify live messages in another terminal:

```bash
bash scripts/ros2-shell.sh /bin/bash -c \
  'source /opt/ros/humble/setup.bash; python3 /root/d1-tools/verify-ros2-sensors.py'
```

The check requires at least two messages on each of 13 sensor topics in 15
seconds. This checks delivery, not sensor calibration, timestamp freshness,
or transform completeness. ROS 2 uses domain 42 and UDP transport so separate
rootless invocations can communicate without shared-memory mounts. Host
networking also makes ROS 1 traffic reachable; this environment is for trusted
robot software, not isolation of untrusted code. No startup service is installed.

The setup script makes two container-only packaging accommodations for a
single-ID namespace: it omits unused sudo configuration snippets and changes
fontconfig's font-directory group from `staff` to namespace root. Host sudo
configuration is untouched. The older Docker installer is an optional
alternative and is not used by this setup.

**Verified live:** the setup script completed successfully, then the ROS 2
acceptance check passed on all 13 topics. In 15 seconds it received 225 scans,
1501 odometry messages, 1484 IMU messages, 425 RGB images, 424 depth images,
and 75 messages on each of eight air-quality topics. Approximate observed
rates were 15 Hz, 100 Hz, 99 Hz, 28 Hz, 28 Hz, and 5 Hz respectively.
See [captured counts and samples](evidence/ros2-sensors-2026-11-14.jsonl).
ROS 2 `tf2_echo base_link front_laser` also resolved the laser transform
(translation 0.197, 0, 0.192 m; identity rotation). This checks one transform,
not the entire tree. A separate ROS 1 timestamp sample showed scan/odometry
ages of about 61/12 ms relative to the host clock.

The [post-start ROS 1 graph check](evidence/ros1-bridge-safety-2026-11-14.json)
found no ROS 1 publishers belonging to the bridge. The sole `/cmd_vel`
publisher remained the vendor motor driver, and motor enable was false.
The bridge is a foreground process, not a persistent startup service; use the
run command above after a reboot or when the process is stopped.

### Follow-up live checks (14 November)

Detailed stand-test results and remaining drive checks are recorded in
[drive validation](drive-validation.md). Motor power is currently off
and motor enable false. A brief speed-feedback peak triggered the latest
test guard; offline analysis found quantized RPM-like values and a mean
rate below the request. Physical overshoot versus reporting artifacts
remains unresolved; no ROS 2 drive route has been enabled.

The stand tests subsequently commanded rotation through the vendor `/cmd_vel`
interface and received `/robot/motor/actual_vel` feedback. After the tests,
`/mot_sbl2360_driver/motor_enable` was `false` and velocity feedback returned
to zero. Physical emergency-stop behavior and command-loss watchdog behavior
still need a dedicated test; these checks do not establish a reliable stop.

A later read-only sensor check received:

| Topic | Observed message |
|---|---|
| `/robot/scan` | 693 ranges; declared limits 0.05–23 m; `front_laser` |
| `/robot/odom` | `nav_msgs/Odometry`, frame `odom` |
| `/robot/imu/data` | `sensor_msgs/Imu`, frame `imu_link` |
| `/camera_back/rgb/image_raw` | 640×480 `rgb8`, 921600 bytes |
| `/camera_back/depth/image_rect_raw` | 640×480 `16UC1`, 614400 bytes |
| `/disinfection/{pm10,pm25,pm100}` | `std_msgs/Float64`, each 5.0 |
| `/disinfection/o3` | `std_msgs/Float64`, 0.197 |
| `/disinfection/tvoc` | `std_msgs/Float64`, 1.042 |
| `/disinfection/{co2,temperature,humidity}` | `std_msgs/Float64`, each 0.0 |

Upper and lower `/depth/image_raw` subscriptions each timed out after four
seconds. All air-quality units, calibration, and zero-reading validity remain
unverified. Image encoding alone does not establish depth units. These are
single-message checks, not rate or timestamp-synchronization verification.
These samples were taken before bridge setup. ROS 2 delivery is now verified
in the rootless environment described above; the host remains on Melodic.

Validate sensor units, calibration, all required transforms, and upper/lower
camera delivery. Inspect the existing motor watchdog and test physical
emergency-stop behavior before adding a ROS 2 command path. Nav2 driving,
a named door goal, and Home Assistant integration have not been demonstrated.

### Stationary SLAM and navigation packages

Install navigation dependencies inside the rootless environment:

```bash
bash scripts/install-navigation.sh
```

This installs Humble SLAM Toolbox, Navigation2, and Nav2 bringup. It starts
no navigation nodes. Single-ID rootless packaging requires root:root 0755
overrides for the D-Bus launch helper and ssh-agent; these apply only inside
the rootfs and remove their normal special privilege bits. No system bus
or SSH service is started. The installation completed with an empty dpkg audit.

With the sensor bridge running, start **SLAM only** in another terminal:

```bash
bash scripts/run-mapping.sh
```

The launcher uses upstream SLAM defaults with `/robot/scan`, `base_link`,
`odom`, `map`, and real time. It creates no command bridge or navigation
controller. Ctrl-C stops mapping. Do not run a second mapper or map-to-odom
publisher alongside it.

The [navigation preflight](evidence/navigation-preflight-2026-11-14.json)
resolved odom-to-base and base-to-laser transforms, with scan/odometry ages
about 90/13 ms in that sample. The
[mapping acceptance](evidence/mapping-acceptance-2026-11-14.json)
received three map messages and resolved map-to-odom. It found no ROS 2
`/cmd_vel` publisher. Motor power and enable were separately checked false.

Saved snapshot: [map metadata](../maps/d1-stationary.yaml) and
[occupancy image](../maps/d1-stationary.pgm). It contains 214 by 309 cells at
0.05 m resolution, including 4,817 known cells. This is a stationary laser
snapshot, not a surveyed room map or evidence of successful navigation.
SLAM remains running in the current session; restart it manually after exit
or reboot. Mapping runs require corrected drive behavior, a validated
watchdog, and the brief's physical supervision requirements before movement.

Follow `tuwrc-d1-brief.md`: UV-C and plasma stay disconnected, first drive
tests on a stand, a person holds the stop during every movement, and autonomous
runs require a mentor. No firmware flashing or mechanical modification.

### ROS 2 drive gate (stand testing pending)

The separate adapter preserves the vendor driver and never calls motor
power/enable services. Build and test it:

```bash
bash scripts/build-drive-gate.sh
g++ -std=c++14 -Wall -Wextra -Werror tests/test_drive_policy.cpp -o /tmp/d1-policy-test
/tmp/d1-policy-test
bash scripts/test-drive-gate.sh
```

The transport test uses a private ROS 1 master on localhost:11312 and ROS 2
domain 43, fake stop status, and a dry-run output. It cannot reach the
robot's ROS master. It checks ten startup, limiting, timeout, stop/release,
and recovery scenarios, including absence of hardware command messages.

`bash scripts/run-drive-gate.sh` uses the live sensor environment but outputs
only to ROS 1 `/d1/dry_run_cmd_vel`. Explicit `--hardware` selects ROS 1
`/cmd_vel`; do not use it without the brief's stand/stop supervision.
The gate starts disarmed. ROS 2 `/d1/drive_arm` (`std_msgs/msg/Bool`) arms only
with fresh released stop status, and clears any old command. ROS 2 `/cmd_vel`
(`geometry_msgs/msg/Twist`) is clamped to 0.10 m/s and 0.08 rad/s. Unsupported
axes or nonfinite values disarm. Stop press, missing stop status (300 ms),
or missing commands (250 ms after a command) latch disarmed. A fresh arm and
new command are needed to resume. `/d1/drive_armed` reports policy state,
not motor power or physical stopping. Only the vendor stop topic is consumed
from ROS 1; vendor self-published commands cannot re-enter the gate.

These are software checks. In-process zero publication does not protect
against a crashed gate, a disconnected ROS link, or controller failure.
Vendor command-loss stopping and bounded physical stand tests remain required
before floor motion or Nav2. The gate is not launched automatically.

**Latest physical stand result:** ROS 2 commands reached the wheels and the
gate latched disarmed after command-stream loss. Small nonzero feedback and
encoder changes persisted after zero commands, so prompt physical stopping
is not established. The vendor motor-enable configuration parameter did not
track runtime enable; use live motor controllable status and power telemetry
as well. Final power was off and velocity zero. See the latest section of
[drive validation](drive-validation.md). Floor/Nav2 motion remains pending.

The operator subsequently reported a quick visible stop during command-stream
loss. A separate adapter-process-loss test showed nonzero feedback through
300–1000 ms after the crash; the vendor's own zero command appeared 1.264 s
after adapter loss. This leaves an independent disable-on-loss supervisor as
a prerequisite for floor/Nav2 use. See [process-loss analysis](evidence/ros2-stand-gate-loss-analysis-2026-11-14.json).
The latest passive error message was specifically motor-power-off, matching
our off state; it does not establish the cause of the separate undervoltage
configuration flag.

### Independent motor watchdog

The independent ROS 1 process watches only commands whose caller ID is
`/d1_drive_gate`. Vendor self-published commands cannot refresh its 150 ms
adapter timer. Once activated, stale emergency/power status (300 ms), stop
press, invalid commands, power loss, or 350 ms of zero commands after motion
latch a trip. It publishes zero and requests motor disable and power off in
separate workers, so a blocked RPC cannot block the other request. It never
requests enable or automatic rearm.

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
bash scripts/test-drive-watchdog.sh
bash scripts/run-drive-watchdog.sh  # dry-run only; no command/service output
```

The integration test uses localhost:11313 with fake motor services. It covers
dry-run, adapter loss with a blocked motor-disable RPC, and orderly shutdown.
`--hardware` selects actual disable outputs; **do not run the hardware gate
alone**. The coordinated stand harness starts both processes and checks
supervisor status before sending commands. With ROS Melodic and the vendor
message PYTHONPATH sourced, its explicit supervised invocation is:
`python2 scripts/stand-ros2-test.py --run --gate-loss --watchdog`.

Startup is two-phase because vendor GPIO power RPCs pause stop/power topic
publication for about half a second. The watchdog first prepares with fresh
safe inputs and power off, accepting only zero commands. Preparation expires
after five seconds. After power-on and fresh telemetry return, explicit
`/d1/drive_supervisor_activate` (`std_msgs/Bool`, ROS 1) activates runtime
checks. `/d1/drive_supervisor_prepared`, `/d1/drive_supervisor_ready` and
`/d1/drive_supervisor_tripped` report the phases. The harness guards against a
trip or physical stop during the blocking power-on call before enabling
motors. The adapter remains disarmed until startup completes.

**Recorded stand result:** following deliberate adapter process loss, the
watchdog sent zero after 159 ms and live motor `ui_srv_call` became false
after 193 ms, before the harness cleanup. Power-off telemetry arrived after
763 ms, overlapping later harness cleanup. These are host receipt timings,
not physical stopping latency. Final power was false and velocity zero.
See [watchdog analysis](evidence/ros2-stand-watchdog-analysis-2026-11-14.json).
The host, supervisor process itself, controller and network remain shared
failure points; physical stop supervision remains required. No floor or
Nav2 motion has been validated.
