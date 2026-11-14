#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
mkdir -p "$rootfs/root/d1-tools"
cp "$repo_dir/scripts/drive-watchdog.py" "$repo_dir/containers/drive_watchdog.py" "$rootfs/root/d1-tools/"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/one/setup.bash
  exec python3 /root/d1-tools/drive-watchdog.py "$@"
' bash "$@"
