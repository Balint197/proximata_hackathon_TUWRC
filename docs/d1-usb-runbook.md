# D1: what we will run after USB connection

Research date: 13 November 2026. This is a proposed runbook, not evidence of a connection or tested D1 drivers. No software has been installed on the robot and no robot commands have been sent. See [hardware research](d1-hardware-research.md) for manufacturer and customs evidence.

## Decision

**Onboard evidence now confirms Ubuntu 18.04.6 LTS.** The Jazzy/Humble package examples below are not applicable to a native installation on this unit. Inspect `/opt/ros`, installed packages, processes, and vendor application directories first. Preserve the existing OS and working drivers; select any container/separate-computer ROS 2 approach only after identifying the current hardware interface. See [connection evidence](d1-connection-check.md).

Use the D1's existing Ubuntu computer for hardware access and ROS 2. Use the Mac for USB enumeration, SSH, editing, and viewing evidence. First preserve and inspect the existing software: it may already contain the only working drivers or protocol descriptions.

Choose **ROS 2 Jazzy for Ubuntu 24.04**, or **Humble for Ubuntu 22.04**, unless an existing supported robot installation gives us a reason to keep its version. These are the distributions' documented Ubuntu binary targets; they are not assertions about the D1's installed OS. Do not upgrade/reimage the robot to make it fit this plan. If Ubuntu is older, first assess whether a matching Ubuntu userspace in a container or a separate Linux computer can use the existing driver; a container does not supply missing kernel drivers. Sources: [Jazzy installation source](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/Ubuntu-Install-Debs.rst), [Humble installation source](https://github.com/ros2/ros2_documentation/blob/humble/source/Installation/Ubuntu-Install-Debs.rst).

The local machine was checked: macOS 26.6.2, arm64, with Python 3, SSH, and a Docker CLI available. A running Docker engine and Linux hardware passthrough have **not** been verified. Native onboard Linux is the preferred execution environment.

## 1. Identify what the cable connects

A USB cable does not imply a remote shell. USB has host and peripheral roles; exposing a serial console or network gadget requires suitable hardware and software on the robot. A regular host port may expose neither. Source: [Linux USB gadget documentation](https://docs.kernel.org/driver-api/usb/gadget.html).

Use the mentor-designated data/service port and cable. Do not improvise a host-to-host USB-A cable. Record the port and original cabling.

On the **Mac**, take these snapshots before and after plugging in:

```sh
system_profiler SPUSBDataType
# On this Mac's macOS version, use the available replacement data type:
system_profiler SPUSBHostDataType
ioreg -p IOUSB -l -w 0
find /dev -maxdepth 1 \( -name 'cu.*' -o -name 'tty.*' \) -print
networksetup -listallhardwareports
ifconfig
```

Interpret the difference, rather than guessing an IP address or baud rate:

| New observation | Next step |
| --- | --- |
| USB network adapter | Inspect that interface's address/route; obtain the robot address and login from its screen or mentor, then SSH. |
| Serial device | Record VID/PID, USB strings and interface class. Establish whether this is a console, a sensor, or a control board before opening it. |
| Camera, scanner, hub, or composite device | Inventory each interface; this may expose a peripheral rather than the Ubuntu computer. |
| Nothing enumerates | Check the data cable and documented port with the mentor. Use the onboard touchscreen terminal or shared Ethernet/Wi-Fi for shell access. |

Opening serial is not necessarily passive: some OS drivers assert RTS/DTR at open, potentially resetting a connected board. Do not begin with `screen`, baud-rate sweeps, arbitrary serial writes, or protocol probes. Source: [pySerial API notes](https://pyserial.readthedocs.io/en/stable/pyserial_api.html).

## 2. Inventory Ubuntu before starting anything

Run these on the **robot**, through its terminal or a known SSH login. Commands query metadata and existing state; missing utilities can simply be recorded. Keep raw output local until reviewed for credentials or private network details.

```sh
cat /etc/os-release
uname -a
uname -m
id
lsusb
lsusb -t
lspci -nnk
ls -l /dev/serial/by-id /dev/serial/by-path /dev/v4l/by-id
ip -br addr
ip -details link show
ip route
ss -lntup
ps -eo pid,comm
systemctl list-units --type=service --state=running --no-pager
ls /opt
ls /opt/ros
dpkg-query -W 'ros-*' 'librealsense*' 'libopenni*'
journalctl -k -b -n 200 --no-pager
```

Next inspect identified service units, application directories, config files, and logs selectively. Find the owning process before touching a device. Do not stop vendor services, unplug internal devices, or start competing drivers during inventory. Record physical port, VID/PID, serial, device path, Linux driver, owning service, observed data, and confidence for each component.

If a running ROS installation exists, source its actual setup file in a separate shell and inspect:

```sh
ros2 node list
ros2 topic list -t
ros2 service list -t
ros2 action list -t
# Substitute an observed topic:
ros2 topic info /scan --verbose
```

These are graph queries, not control commands. An empty graph does not prove no ROS is running: first check the selected distribution, domain ID, middleware configuration, network, and whether the vendor uses ROS 1. Source: [ROS 2 topic inspection documentation](https://github.com/ros2/ros2_documentation/blob/rolling/source/ROS-Framework/interfaces/topics/Understanding-ROS2-Topics/Understanding-ROS2-Topics.rst).

## 3. Tools selected by actual evidence

| Task | What we would run | Condition |
| --- | --- | --- |
| Discovery | `usbutils`, `pciutils`, `iproute2`, systemd tools, `lsof` | Use existing commands first; add missing tools after checking package changes. |
| Existing USB traffic | Linux `usbmon`, optionally Wireshark/tshark | Capture on the Ubuntu host that actually owns the device. A Mac plugged into another port cannot see arbitrary internal USB traffic. |
| Existing network traffic | Bounded `tcpdump` on the identified robot interface | Start with metadata and narrow captures; no discovery sweeps on the event network. |
| RGB/depth camera | `v4l2-ctl --list-devices`, then a matching vendor SDK/ROS 2 driver | A UVC video stream alone does not prove access to depth or calibration. Do not assume RealSense, Orbbec, or OpenNI. |
| LiDAR | Existing driver, otherwise the identified manufacturer's ROS 2 driver | Require actual model, transport, configuration, and frame geometry. Do not assume RPLIDAR, YDLIDAR, SICK, or Hokuyo. |
| Serial/CAN boards | Existing application/config first; capture known traffic if available | Do not assume Modbus, CANopen, baud rate, arbitration IDs, wheel layout, or units. No blind writes or bus reconfiguration. |
| Air sensors / LEDs / digits | Small ROS 2 adapter only after decoding the real protocol | Isolate disinfection outputs; observing a shared board does not authorize writing arbitrary registers. |

`usbmon` is Linux host-side USB monitoring and needs kernel support/debugfs and potentially elevated access. It is a later diagnostic, not a reason to unbind working drivers. Source: [kernel usbmon documentation](https://kernel.org/doc/html/latest/usb/usbmon.html).

## 4. ROS software we aim to run

This is our proposed application stack, not a discovered D1 API:

```text
sensor drivers/adapters -> /scan, camera topics, air-quality topics
base adapter           -> /odom, odom -> base_link TF, diagnostics
robot_state_publisher  -> measured sensor/static frame geometry
SLAM Toolbox           -> map while mapping
Nav2 + AMCL            -> localization and navigation on a saved map
teleop / Nav2           -> command selection -> limits/collision checks
                       -> base adapter with watchdog -> motor controller
Home Assistant MQTT    -> door-goal bridge -> Nav2 NavigateToPose
onboard browser        -> authenticated door-camera dashboard
rosbag2 + RViz2         -> recordings and visual verification
```

Use a minimal ROS base on constrained hardware; run RViz on a separate Linux machine if needed. Add navigation packages only after sensor/drive bringup. Candidate Debian packages, **after** the correct ROS apt repository is configured and package changes are reviewed:

```sh
# Ubuntu robot only. Example for a confirmed 24.04/Jazzy installation.
# Set d1_ros_distro=humble instead only on a confirmed 22.04/Humble setup.
d1_ros_distro=jazzy
apt-cache policy "ros-${d1_ros_distro}-ros-base" \
  "ros-${d1_ros_distro}-navigation2" "ros-${d1_ros_distro}-slam-toolbox"
sudo apt-get -s install "ros-${d1_ros_distro}-ros-base" \
  "ros-${d1_ros_distro}-navigation2" "ros-${d1_ros_distro}-nav2-bringup" \
  "ros-${d1_ros_distro}-slam-toolbox" "ros-${d1_ros_distro}-robot-state-publisher" \
  "ros-${d1_ros_distro}-teleop-twist-keyboard" "ros-${d1_ros_distro}-rosbag2"
```

`-s` simulates installation. Do not execute a real install if it would remove or replace critical vendor/system packages. No blanket OS upgrades. Real launch commands must wait for measured configuration; default Nav2 configs are not D1 configs.

Nav2 needs consistent transforms, sensor inputs, odometry, and an actual collision footprint. Start from the brief's 0.58 m × 0.58 m envelope only as a planning clue; measure protrusions and clearance before autonomous motion. Use `map -> odom -> base_link -> sensor` with one publisher per transform. Validate timestamps, frame axes, scan orientation, encoder scale and turning sign. Source: [Nav2 robot setup guide](https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/).

SLAM Toolbox is the selected 2D mapping candidate, using laser scans and odometry transforms. Save a map and localize against it for repeatable door runs; do not run competing publishers of `map -> odom`. Source: [SLAM Toolbox upstream](https://github.com/SteveMacenski/slam_toolbox).

Inspect the actual `/cmd_vel` message type end to end. Nav2 changed the default from `Twist` to `TwistStamped` in Kilted; Jazzy also supports opting into stamped messages. Set `enable_stamped_cmd_vel` consistently on nodes that support it and adapt the base interface deliberately. Source: [Nav2 migration guide](https://docs.nav2.org//rolling/configuration_and_development/migration_guides/jazzy/Jazzy/).

## 5. Drive bringup gates

The [brief](../tuwrc-d1-brief.md) requires disconnected UV-C/plasma hardware, initial drive tests on a stand, a person with a hand on the stop for all movement, walking pace at most within the marked area, and a mentor for autonomy. No firmware flashing or destructive access.

Before enabling any drive command:

1. Identify the physical stop and have the mentor demonstrate its effect. Establish controller behavior on cable loss, process death, and stale commands.
2. Keep motor enable disabled while decoding traffic. Map motor commands separately from disinfection commands; no guessed register writes.
3. Put the robot on the approved stand. Test the physical stop and controller timeout with minimal wheel commands, then check direction and encoder feedback one step at a time.
4. Implement limits and command expiry in the base adapter. A proposed initial target is 0.05 m/s linear and 0.1 rad/s angular, with a 250 ms stale-command cutoff; these are engineering starting values, **not verified D1 limits**. Confirm the controller's own watchdog; a software adapter cannot stop motors if the adapter or computer freezes and the controller keeps its last command.
5. Verify deadman release, timeout, killed driver, disconnected control link, and stop/reset behavior on the stand. Reset must not resume an old command. Only then move to supervised floor tests and tune limits to the measured stopping distance.

Route teleop and navigation through one command authority; do not leave another publisher able to bypass the final checks. Nav2 Collision Monitor can add obstacle-based software stopping but does not provide hard real-time safety certification and does not replace the physical stop. Source: [Collision Monitor](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/).

## 6. Doorbell integration

Prefer the event's existing Home Assistant MQTT broker; do not install a second broker without need. Confirm MQTT is available when credentials arrive. If it is unavailable, use the existing HA REST/WebSocket interfaces as a separate implementation choice.

Proposed flow: the real doorbell entity/event triggers an HA automation, which publishes a non-retained `d1/mission/request` message. A Python ROS node validates a unique event ID, short expiry and allowlisted goal `door`, checks an explicit armed state and Nav2 readiness, and sends a `nav2_msgs/action/NavigateToPose` goal. Deduplicate QoS redelivery, reject retained/stale requests, ignore repeats while busy, and never restart a goal automatically after reconnect. Publish accepted/running/arrived/failed state to `d1/mission/state`.

This is a proposed bridge to write, not an existing package. MQTT carries mission requests, never raw wheel commands. Sources: [HA MQTT integration](https://www.home-assistant.io/integrations/mqtt/), [HA MQTT publish action](https://www.home-assistant.io/actions/mqtt.publish/).

On the robot display, use an authenticated browser view with the actual HA camera entity and `camera_view: live`, subject to the camera's supported streaming modes. Validate the feed before the demo; keep HA credentials out of the public repo and command-line history. Source: [HA picture entity card](https://www.home-assistant.io/dashboards/picture-entity/).

## 7. Evidence and time priorities

First session: enumerate USB, gain a legitimate shell, preserve the current software inventory, identify devices and owners, then obtain **one live sensor stream**. The motor protocol is a parallel uncertainty, not a prerequisite for documenting sensors.

Next: bring up remaining sensors and timestamped ROS recordings; establish tested stop/odometry/drive; only then map and navigate. Home Assistant integration can be exercised against a simulated Nav2 robot in a separate ROS domain while hardware access is blocked. Keep simulation isolated from the real command graph.

For the public handoff, collect a redacted interface table, exact package versions, launch/config files, map and door pose, selected rosbag recordings, measured stop-test results, and the brief's three-minute demo video. Do not describe simulation, guessed hardware models, or a topic merely appearing in `ros2 topic list` as live hardware success.

### Open facts to resolve on connection

- Which USB port and mode are exposed, and whether it reaches Ubuntu at all.
- Ubuntu version/architecture, login and privileges, installed ROS/vendor software.
- LiDAR and depth-camera models, interfaces, and calibration.
- Motor protocol, controller watchdog, physical stop behavior, encoder units and wheel geometry.
- Air sensor/LED board protocols and separation from disabled disinfection hardware.
- HA endpoint, doorbell event, camera entity, broker access, and measured door pose.
