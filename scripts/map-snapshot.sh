#!/usr/bin/env bash
# Save the live SLAM map and render it (1 m grid, robot pose, named goals) to PNG.
# Usage: bash scripts/map-snapshot.sh [name]   -> maps/<name>.{pgm,yaml,png}
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
name="${1:-live}"
mkdir -p "$rootfs/root/d1-tools/maps"
cp "$repo_dir/scripts/robot_pose.py" "$rootfs/root/d1-tools/"
bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -c "source /opt/ros/humble/setup.bash
  ros2 run nav2_map_server map_saver_cli -f /root/d1-tools/maps/$name --ros-args -p save_map_timeout:=10.0 >/dev/null 2>&1" 
pose=$(bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -c 'source /opt/ros/humble/setup.bash; python3 /root/d1-tools/robot_pose.py' 2>/dev/null | tail -1)
cp "$rootfs/root/d1-tools/maps/$name.pgm" "$rootfs/root/d1-tools/maps/$name.yaml" "$repo_dir/maps/"
marks=$(python3 - "$pose" "$repo_dir/config/places.yaml" <<'PY'
import json, sys, os, yaml
out = []
try:
    p = json.loads(sys.argv[1]); out.append('robot,%f,%f,%f' % (p['x'], p['y'], p['yaw']))
except Exception: pass
if os.path.exists(sys.argv[2]):
    for k, v in (yaml.safe_load(open(sys.argv[2])) or {}).get('places', {}).items():
        out.append('%s,%f,%f,%f' % (k, v['x'], v['y'], v['yaw']))
print(' '.join(out))
PY
)
python3 "$repo_dir/scripts/render_map.py" "$repo_dir/maps/$name" "$repo_dir/maps/$name.png" $marks
echo "pose: $pose"
