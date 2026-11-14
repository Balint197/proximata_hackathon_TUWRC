#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
mkdir -p "$rootfs/root/d1-tools/nav2"
cp "$repo_dir"/config/nav2_preview.launch.py "$repo_dir"/config/navigate_preview.xml "$repo_dir"/config/navigate_through_preview.xml "$rootfs/root/d1-tools/nav2/"
cp "$repo_dir/scripts/prepare-nav2-preview.py" "$rootfs/root/d1-tools/nav2/"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/humble/setup.bash
  python3 /root/d1-tools/nav2/prepare-nav2-preview.py
  exec ros2 launch /root/d1-tools/nav2/nav2_preview.launch.py
'
