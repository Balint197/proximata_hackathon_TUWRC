#!/usr/bin/env bash
set -u

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUT_DIR="d1_recon_${TIMESTAMP}"
mkdir -p "${OUT_DIR}"

echo "[*] Starting D1 hardware and system discovery -> ${OUT_DIR}/"

# 1. OS, kernel, environment variables, and installed ROS distributions
{
  echo "=== UNAME ==="
  uname -a
  echo -e "\n=== OS RELEASE ==="
  cat /etc/os-release 2>/dev/null
  echo -e "\n=== ENV ==="
  env
  echo -e "\n=== ROS INSTALLATIONS ==="
  ls -la /opt/ros/ 2>/dev/null
} > "${OUT_DIR}/01_system_env.txt"

# 2. USB devices and serial ports (identifies 3D camera, LiDAR, and USB-UART adapters)
{
  echo "=== LSUSB ==="
  lsusb
  echo -e "\n=== LSUSB TREE ==="
  lsusb -t
  echo -e "\n=== SERIAL BY-ID ==="
  ls -la /dev/serial/by-id/ 2>/dev/null
  echo -e "\n=== SERIAL BY-PATH ==="
  ls -la /dev/serial/by-path/ 2>/dev/null
  echo -e "\n=== TTY / VIDEO / I2C / SPI DEVICES ==="
  ls -la /dev/ttyUSB* /dev/ttyACM* /dev/ttyS* /dev/video* /dev/i2c* /dev/spidev* 2>/dev/null
} > "${OUT_DIR}/02_usb_serial_devices.txt"

# 3. Udev rules (commercial robots often define named symlinks like /dev/lidar or /dev/mcu here)
{
  echo "=== /etc/udev/rules.d/ ==="
  ls -la /etc/udev/rules.d/
  head -n 200 /etc/udev/rules.d/* 2>/dev/null
} > "${OUT_DIR}/03_udev_rules.txt"

# 4. Kernel ring buffer logs for attached peripherals
dmesg | grep -iE "tty|usb|serial|uvc|can|eth|wlan|ftdi|cp210|ch340|pl2303|lidar|realsense|orbbec" > "${OUT_DIR}/04_dmesg_filtered.txt" 2>/dev/null

# 5. Network interfaces, open sockets, and CAN buses (for Ethernet LiDAR or internal subnets)
{
  echo "=== IP A ==="
  ip a
  echo -e "\n=== IP ROUTE ==="
  ip route
  echo -e "\n=== ARP TABLE ==="
  arp -a 2>/dev/null || ip neigh
  echo -e "\n=== OPEN PORTS (SS) ==="
  ss -tulnp 2>/dev/null
  echo -e "\n=== CAN INTERFACES ==="
  ip link show type can 2>/dev/null
} > "${OUT_DIR}/05_network_can.txt"

# 6. Running services and existing ROS packages on the filesystem
{
  echo "=== SYSTEMD SERVICES ==="
  systemctl list-units --type=service --all --no-pager
  echo -e "\n=== EXISTING ROS PACKAGES (/home, /opt, /root) ==="
  find /home /opt /root -maxdepth 4 -name "package.xml" 2>/dev/null
  echo -e "\n=== RUNNING PROCESSES ==="
  ps aux
} > "${OUT_DIR}/06_services_and_code.txt"

# 7. Audio devices (for the voice interaction bonus task)
{
  echo "=== ARECORD (Capture Devices) ==="
  arecord -l 2>/dev/null
  echo -e "\n=== APLAY (Playback Devices) ==="
  aplay -l 2>/dev/null
} > "${OUT_DIR}/07_audio_hardware.txt"

tar -czf "${OUT_DIR}.tar.gz" "${OUT_DIR}"
echo "[+] Done! Archive created: ${OUT_DIR}.tar.gz"
echo "[+] Copy to your laptop: scp hrc@<d1_ip>:~/${OUT_DIR}.tar.gz ."