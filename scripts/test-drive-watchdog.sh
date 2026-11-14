#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
mkdir -p "$rootfs/root/d1-tools"
cp "$repo_dir/scripts/drive-watchdog.py" "$repo_dir/containers/drive_watchdog.py" \
  "$repo_dir/tests/watchdog_transport.py" "$rootfs/root/d1-tools/"
bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  export ROS_MASTER_URI=http://127.0.0.1:11313 ROS_IP=127.0.0.1
  source /opt/ros/one/setup.bash
  roscore -p 11313 >/tmp/watchdog-test-master.log 2>&1 & master=$!
  trap "kill $master 2>/dev/null || true" EXIT
  for attempt in $(seq 1 50); do
    if rosparam list >/dev/null 2>&1; then break; fi
    sleep .1
  done
  python3 /root/d1-tools/watchdog_transport.py
'
