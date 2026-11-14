#!/usr/bin/env bash
# Host wrapper for the supervised drive session (ROS Melodic + vendor messages).
# Usage: bash scripts/run-session.sh [session options] -- <ROS 2 command>
# A person must hold the physical stop during every session (house rules).
set -eo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/melodic/setup.bash
export PYTHONPATH="$HOME/clobot_ws/devel/lib/python2.7/dist-packages:$PYTHONPATH"
export ROS_MASTER_URI=http://192.168.0.4:11311 ROS_IP=192.168.0.2
exec python2 "$repo_dir/scripts/drive-session.py" --run "$@"
