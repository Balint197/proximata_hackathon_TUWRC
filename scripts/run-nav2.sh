#!/usr/bin/env bash
# Live Nav2 for the D1 (needs run-sensor-bridge.sh and run-mapping.sh running).
# Output goes to ROS 2 /cmd_vel -> drive gate, which stays disarmed outside a
# supervised drive session (run-session.sh). Ctrl-C stops it.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
mkdir -p "$rootfs/root/d1-tools/nav2"
cp "$repo_dir"/config/nav2_live.launch.py "$repo_dir"/config/prepare-nav2.py \
   "$repo_dir"/config/navigate_preview.xml "$repo_dir"/config/navigate_through_preview.xml \
   "$rootfs/root/d1-tools/nav2/"
cp "$repo_dir"/scripts/d1_scan_filter.py "$repo_dir"/scripts/session_checks.py "$rootfs/root/d1-tools/"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/humble/setup.bash
  python3 /root/d1-tools/nav2/prepare-nav2.py
  exec ros2 launch /root/d1-tools/nav2/nav2_live.launch.py
'
