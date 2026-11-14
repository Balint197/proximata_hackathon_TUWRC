#!/usr/bin/env bash
# Install navigation tools inside the account-owned rootfs; start no nodes.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$repo_dir/scripts/ros2-shell.sh" /bin/bash -ec '
  export DEBIAN_FRONTEND=noninteractive
  # Single-ID namespaces cannot assign messagebus/_ssh ownership. The final
  # install below must succeed; this first pass may stop at those postinsts.
  apt-get install -y --no-install-recommends \
    ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup || true
  for helper in /usr/lib/dbus-1.0/dbus-daemon-launch-helper /usr/bin/ssh-agent; do
    if test -f "$helper" && ! dpkg-statoverride --list "$helper" >/dev/null; then
      dpkg-statoverride --update --add root root 0755 "$helper"
    fi
  done
  dpkg --configure -a
  apt-get install -y --no-install-recommends \
    ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup
  dpkg --audit
'
