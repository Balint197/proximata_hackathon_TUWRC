#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
source_dir="$rootfs/root/drive-gate-src"
mkdir -p "$source_dir"
cp "$repo_dir/containers/d1_drive_gate.cpp" "$repo_dir/containers/drive_policy.hpp" "$source_dir/"
cp "$repo_dir/containers/drive-gate.cmake" "$source_dir/CMakeLists.txt"
bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/one/setup.bash
  unset ROS_DISTRO
  source /opt/ros/humble/setup.bash
  cmake -S /root/drive-gate-src -B /root/drive-gate-build \
    -Dgeometry_msgs_DIR=/opt/ros/humble/share/geometry_msgs/cmake \
    -Dstd_msgs_DIR=/opt/ros/humble/share/std_msgs/cmake \
    -Drosgraph_msgs_DIR=/opt/ros/humble/share/rosgraph_msgs/cmake
  cmake --build /root/drive-gate-build -j2
  install -m755 /root/drive-gate-build/d1_drive_gate /root/d1-tools/d1_drive_gate
'
