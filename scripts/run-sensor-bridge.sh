#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/one/setup.bash
  unset ROS_DISTRO
  source /opt/ros/humble/setup.bash
  source /root/bridge_ws/install/local_setup.bash
  exec /root/bridge_ws/install/ros1_bridge/lib/ros1_bridge/static_bridge
'
