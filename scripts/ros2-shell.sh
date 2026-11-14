#!/usr/bin/env bash
# Rootless Ubuntu environment. Host networking; no host devices or ROS mounts.
set -euo pipefail
rootfs="${D1_ROS2_ROOTFS:-$HOME/.local/share/d1-ros2/rootfs}"
test -x "$rootfs/bin/bash" || { echo 'Ubuntu rootfs is not installed.' >&2; exit 1; }
if (($# == 0)); then set -- /bin/bash; fi
exec env -i PATH=/usr/bin:/bin bwrap --unshare-user --uid 0 --gid 0 --unshare-pid --unshare-ipc \
  --die-with-parent --new-session --bind "$rootfs" / \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind /etc/resolv.conf /etc/resolv.conf \
  --setenv HOME /root --setenv USER root \
  --setenv PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  --setenv LANG C.UTF-8 --setenv TERM "${TERM:-xterm}" \
  --setenv ROS_MASTER_URI http://192.168.0.4:11311 \
  --setenv ROS_IP 192.168.0.2 --setenv ROS_DOMAIN_ID 42 \
  --setenv FASTRTPS_DEFAULT_PROFILES_FILE /root/d1-tools/fastdds.xml \
  --chdir /root "$@"
