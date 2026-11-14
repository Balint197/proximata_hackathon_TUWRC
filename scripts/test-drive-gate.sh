#!/usr/bin/env bash
# Entire ROS test is isolated: private ROS 1 master and ROS 2 domain 43.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
mkdir -p "$rootfs/root/d1-tools/drive-tests"
cp "$repo_dir"/tests/*drive*py "$rootfs/root/d1-tools/drive-tests/"
bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  export ROS_MASTER_URI=http://127.0.0.1:11312 ROS_IP=127.0.0.1 ROS_DOMAIN_ID=43
  source /opt/ros/one/setup.bash
  roscore -p 11312 > /tmp/test-master.log 2>&1 & master=$!
  trap "kill $master ${recorder:-} ${gate:-} 2>/dev/null || true" EXIT
  for attempt in $(seq 1 50); do
    if rosparam list >/dev/null 2>&1; then break; fi
    sleep .1
  done
  python3 /root/d1-tools/drive-tests/drive_transport_ros1.py > /tmp/test-ros1.log 2>&1 & recorder=$!
  (
    unset ROS_DISTRO
    source /opt/ros/humble/setup.bash
    exec /root/d1-tools/d1_drive_gate
  ) > /tmp/test-gate.log 2>&1 & gate=$!
  (
    unset ROS_DISTRO
    source /opt/ros/humble/setup.bash
    python3 /root/d1-tools/drive-tests/drive_transport_ros2.py
  )
  wait "$recorder"
  python3 /root/d1-tools/drive-tests/check_drive_transport.py
'
