#!/usr/bin/env bash
# Save the robot's current map pose as a named place in config/places.yaml.
# Usage: bash scripts/save-place.sh door        (SLAM must be running)
#        bash scripts/save-place.sh door 2.0 -1.0 1.57   (explicit map x y yaw)
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
name="${1:?place name}"
if (($# == 4)); then
  pose="{\"x\": $2, \"y\": $3, \"yaw\": $4}"
else
  cp "$repo_dir/scripts/robot_pose.py" "$rootfs/root/d1-tools/"
  pose=$(bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -c \
    'source /opt/ros/humble/setup.bash; python3 /root/d1-tools/robot_pose.py' 2>/dev/null | tail -1)
fi
python3 - "$repo_dir/config/places.yaml" "$name" "$pose" <<'PY'
import json, os, sys, yaml
path, name, pose = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
data = yaml.safe_load(open(path)) if os.path.exists(path) else None
data = data or {'frame': 'map', 'places': {}}
data['places'][name] = {k: round(float(pose[k]), 3) for k in ('x', 'y', 'yaw')}
yaml.safe_dump(data, open(path, 'w'), default_flow_style=False)
print('saved', name, data['places'][name])
PY
cp "$repo_dir/config/places.yaml" "$rootfs/root/d1-tools/places.yaml"
