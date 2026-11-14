# D1 connection check — 13 November 2026

Initial check after the team connected the robot to the Mac by USB, around 21:12 local time.

## Observed

- `ioreg -p IOUSB -w 0` lists the Mac's two USB host controllers and no attached peripheral beneath them.
- `ioreg -r -c IOUSBHostDevice -w 0` returns no attached USB host-device entries.
- The only serial endpoints are macOS debug-console and Bluetooth incoming-port endpoints. No USB serial endpoint is exposed.
- Wired/Thunderbolt network interfaces are inactive. Wi-Fi is active, but no robot address has been identified.
- This macOS version exposes `SPUSBHostDataType` rather than `SPUSBDataType`. The correct `system_profiler SPUSBHostDataType` confirms two empty USB buses. Thunderbolt/USB4 also reports no attached device.

No robot shell is available through this connection, so the onboard inventory, sensor drivers, and ROS bringup have not been run. No control commands or firmware changes were sent.

## Interpretation and next experiment

The Mac has not enumerated a robot USB peripheral. This does **not** establish whether the cable is charge-only/bad, the robot port is faulty, or that port is a host port with no peripheral/gadget mode. The team reports that another team suspects this port and that the alternative port is occupied.

Change one variable first: try the second suitable data cable in the same port and rerun USB enumeration. Do not disturb the other team's occupied port. If neither cable enumerates, use the robot's Ubuntu terminal to obtain its IP address (`ip -br addr`) and inspect its own USB tree (`lsusb -t`); a shared network and known SSH login can bypass this USB path.

The team then confirmed a second cable connected to the same port. A fresh `system_profiler SPUSBHostDataType`, IORegistry, serial endpoint, and network-status check produced the same result: empty USB buses, no USB serial endpoint, and no active wired link. Changing the cable did not establish access. This increases suspicion of the port or its role, but neither cable has independently been verified as data-capable.

Next practical access path: use the onboard Ubuntu terminal to obtain its address with `ip -br addr`, then establish shared-network reachability and an SSH login. The occupied alternative port has not been tested or disturbed. A standard cable with USB-A plugs at both ends should not be used to join two host ports.

## Alternative port check

The team subsequently reported WLAN unavailable, the touchscreen in use by another team, and a USB connection moved to the other robot port. Fresh USB profiler, IORegistry, serial endpoint and network checks again showed no attached USB device, no USB serial endpoint, and no active wired link. Thus the newly attempted port has not established Mac-side access either. Whether these robot sockets are ordinary USB host ports remains unresolved; connector type, port labels, and cable/adapter details are needed before selecting another USB access method. The WLAN failure is team-reported, not independently diagnosed here.

## Clarifications and terminal handoff

The team confirmed a robot USB-A socket connected directly to the Mac's USB-C socket, without an adapter. They also report the cable transferred data with a phone. This makes an ordinary host-to-host connection a stronger explanation than assuming a faulty cable; the robot's USB controller role has not been inspected onboard.

The other team reportedly reached Google with `ping` from the built-in screen. Therefore internet connectivity existed at the time of that test; which interface supplied it remains unknown. No physical Ethernet socket or additional ports were reported. The keyboard is attached at the built-in display, and terminal access is expected soon.

When terminal access is available, first collect `cat /etc/os-release`, `whoami`, `ip -br addr`, `ip route`, `nmcli device status`, `lsusb`, `lsusb -t`, and `ss -lnt`. Do not reconfigure networking until the existing active path and shared use are understood.

An Android phone in USB-tethering mode is a candidate network peripheral for the robot's USB host port. Ubuntu documents phone USB tethering as a mobile broadband connection: [Ubuntu help](https://help.ubuntu.com/stable/ubuntu-help/net-mobile.html.en). This is a candidate, not a tested connection on this unit. Internet access alone does not establish inbound SSH reachability from the Mac; a phone's Wi-Fi-hotspot and USB-tethered clients may be routed separately or isolated. Confirm actual addresses, forwarding, and the SSH listener before relying on that topology.

## Terminal photographs received

### Subsequent gateway and tethering results

Photos 1794604137051.jpg and 1794604410685.jpg establish the following sequence:

- The original gateway `192.168.0.1` failed neighbor resolution (`FAILED`); ping reported Destination Host Unreachable from the robot itself (`192.168.0.2`). Another neighbor, `192.168.0.4`, was REACHABLE, so the existing Ethernet link still had a responding peer. Do not replace its configuration.
- A new USB-path interface `enp0s20f0u6` acquired `10.51.8.42/24` and a DHCP default route through `10.51.8.30` with metric 101, preferred over the original static default's metric 20100.
- The subsequent `ping -c 3 8.8.8.8` received all three replies (0% loss). Outbound IPv4 connectivity is now demonstrated; DNS, VPS SSH, and inbound Mac access still need independent checks.
- A workspace `~/hyundai_ws/src/devel/lib` contains `d1_test` and a `pkgconfig/d1_test.pc` file. This is evidence of an existing built package, not proof of its protocol, ROS version, or safe execution. Inspect source/configuration before running this executable.

Read from the team's three terminal photos (filenames 1794602432069.jpg, 1794602432083.jpg, 1794602432092.jpg):

- Ubuntu 18.04.6 LTS (Bionic); login and hostname both `hrc`.
- `enp1s0` is UP at `192.168.0.2/24`, with a static default route through `192.168.0.1`. NetworkManager calls the connection `netplan-enp1s0`.
- `enp2s0` is DOWN/unavailable. No Wi-Fi or USB-tether network interface appears in this snapshot. The active Ethernet link may be internal; the photos do not establish physical accessibility or its upstream topology.
- TCP port 22 listens on `[::]`. This is consistent with an SSH server, but the process and successful authentication remain unverified. Many other TCP services are already listening; inspect their owners rather than starting replacements.
- USB IDs: `2bc5:0401` (two devices), `266e:0102`, Logitech keyboard `046d:c31c`, and Linux root hubs. The two `2bc5:0401` devices each expose audio interfaces plus an interface claimed by `usbfs`. They are candidates for Orbbec Astra devices: [Orbbec's upstream rules](https://github.com/orbbec/ros_astra_camera/blob/main/56-orbbec-usb.rules) map this VID/PID to `astra`. Exact models, device roles, and data availability still need confirmation. Do not start a competing camera driver.

A bounded Mac TCP connection to the observed `192.168.0.2:22` timed out. The Mac remained `10.10.46.4` and routed that destination through `10.10.40.1` on Wi-Fi, rather than a direct robot link. No login was attempted. Next obtain a shared/reachable network, or inspect from the built-in terminal. Preserve `enp1s0`, which may serve the robot's internal components.
