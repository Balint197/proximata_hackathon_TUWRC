#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/one/setup.bash
  unset ROS_DISTRO
  source /opt/ros/humble/setup.bash
  exec /root/d1-tools/d1_drive_gate "$@"
' bash "$@"
