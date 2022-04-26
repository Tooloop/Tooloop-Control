#!/bin/bash

if [ $EUID != 0 ]; then
  echo "This script must be run as root."
  exit $exit_code
    exit 1
fi

apt install -y \
    python3-pip \
    python3-augeas \
    # python3-crontab \
    # python3-pexpect \
    python3-apt \
    aptitude

pip install Flask pexpect python-crontab