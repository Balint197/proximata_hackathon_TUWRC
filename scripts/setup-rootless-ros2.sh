#!/usr/bin/env bash
# Installs only into ~/.local/share/d1-ros2. No sudo or host package changes.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
data_dir="$HOME/.local/share/d1-ros2"
rootfs="${D1_ROS2_ROOTFS:-$data_dir/rootfs}"
test "$(uname -m)" = x86_64 || { echo 'This setup currently targets x86_64.' >&2; exit 1; }
command -v bwrap >/dev/null
mkdir -p "$data_dir/downloads" "$rootfs"
if ! test -x "$rootfs/bin/bash"; then
  wget -O "$data_dir/downloads/ubuntu-base.tar.gz" \
    https://cdimage.ubuntu.com/ubuntu-base/releases/22.04/release/ubuntu-base-22.04-base-amd64.tar.gz
  echo "df6fe77cee11bd216ac532f0ee082bdc4da3c0cc1f1d9cb20f3f743196bc4b07  $data_dir/downloads/ubuntu-base.tar.gz" | sha256sum -c -
  tar --no-same-owner -xzf "$data_dir/downloads/ubuntu-base.tar.gz" -C "$rootfs"
fi
bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  echo "APT::Sandbox::User \"root\";" > /etc/apt/apt.conf.d/99rootless
  printf "#!/bin/sh\nexit 101\n" > /usr/sbin/policy-rc.d
  chmod +x /usr/sbin/policy-rc.d
  # Single-ID user namespaces cannot unpack sudo group-owned configuration.
  # sudo is unused inside this environment; this excludes only its snippets.
  echo "path-exclude=/etc/sudoers.d/*" > /etc/dpkg/dpkg.cfg.d/rootless-sudo
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates wget gnupg locales
  mkdir -p /etc/apt/keyrings
  wget -qO /etc/apt/keyrings/ros2.gpg https://raw.githubusercontent.com/ros/rosdistro/master/ros.key
  wget -qO /etc/apt/keyrings/ros-one.gpg https://ros.packages.techfak.net/gpg.key
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/ros2.gpg] http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/ros-one.gpg] https://ros.packages.techfak.net jammy main" > /etc/apt/sources.list.d/ros1.list
  apt-get update
  # fontconfig uses group staff, absent from our single-ID mapping. Repair
  # that container-only postinst after unpacking, then finish configuration.
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ros-humble-ros-base ros-one-ros-base ros-one-common-msgs ros-one-tf2-msgs \
    python3-colcon-common-extensions git build-essential || true
  if test -f /var/lib/dpkg/info/fontconfig-config.postinst; then
    sed -i "s/chown root:staff/chown root:root/" /var/lib/dpkg/info/fontconfig-config.postinst
  fi
  DEBIAN_FRONTEND=noninteractive apt-get -f install -y
  # Repairing dependencies alone may omit requested packages after a failed
  # download. Retry the full request and require success this time.
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ros-humble-ros-base ros-one-ros-base ros-one-common-msgs ros-one-tf2-msgs \
    python3-colcon-common-extensions git build-essential
  dpkg --audit
  mkdir -p /root/bridge_ws/src
  if ! test -d /root/bridge_ws/src/ros1_bridge/.git; then
    git clone https://github.com/ros2/ros1_bridge.git /root/bridge_ws/src/ros1_bridge
  fi
  cd /root/bridge_ws/src/ros1_bridge
  git checkout 611755fd917285316051cbea80507e8b2f6b7ec1
'
mkdir -p "$rootfs/root/d1-tools"
cp "$repo_dir/scripts/verify-ros2-sensors.py" "$rootfs/root/d1-tools/"
cp "$repo_dir/containers/fastdds.xml" "$rootfs/root/d1-tools/"
cp "$repo_dir/containers/d1_sensor_bridge.cpp" "$rootfs/root/bridge_ws/src/ros1_bridge/src/static_bridge.cpp"
bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  source /opt/ros/one/setup.bash
  unset ROS_DISTRO
  source /opt/ros/humble/setup.bash
  cd /root/bridge_ws
  MAKEFLAGS=-j4 colcon build --packages-select ros1_bridge --executor sequential \
    --cmake-args -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release
'
