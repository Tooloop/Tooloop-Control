#!/bin/bash

if [ $EUID != 0 ]; then
  echo "This script must be run as root."
  exit $exit_code
    exit 1
fi

apt install -y \
    python3-pip \
    python3-augeas \
    python3-apt \
    python3-venv \
    aptitude

python3 -m venv --system-site-packages venv
. venv/bin/activate
pip install Flask pexpect python-crontab