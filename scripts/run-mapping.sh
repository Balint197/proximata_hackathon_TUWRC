#!/usr/bin/env bash
# SLAM only: consumes laser/TF, produces map/TF, sends no motor commands.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/humble/setup.bash
  python3 - <<"PY"
import yaml
from pathlib import Path
source = Path("/opt/ros/humble/share/slam_toolbox/config/mapper_params_online_async.yaml")
config = yaml.safe_load(source.read_text())
params = config["slam_toolbox"]["ros__parameters"]
params.update(base_frame="base_link", odom_frame="odom", map_frame="map",
              scan_topic="/robot/scan", use_sim_time=False,
              min_laser_range=0.05, max_laser_range=20.0)
Path("/root/d1-tools/mapper_params.yaml").write_text(yaml.safe_dump(config))
PY
  exec ros2 launch slam_toolbox online_async_launch.py \
    use_sim_time:=false slam_params_file:=/root/d1-tools/mapper_params.yaml
'
