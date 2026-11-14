#!/usr/bin/env bash
# Run interactively on the robot. sudo prompts locally; never share passwords.
set -euo pipefail
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y docker.io
fi
sudo systemctl start docker
sudo docker version
sudo docker run --rm hello-world
