#!/bin/bash

if [ $EUID != 0 ]; then
  echo "This script must be run as root."
  exit $exit_code
    exit 1
fi

# install system packages
apt install -y \
    python3-pip \
    python3-augeas \
    python3-apt \
    python3-venv \
    aptitude

# create virtual environment
python3 -m venv --system-site-packages /opt/tooloop/control-center/venv

# install site packages
/opt/tooloop/control-center/venv/bin/pip install --upgrade pip
/opt/tooloop/control-center/venv/bin/pip install Flask Flask-Markdown pexpect python-crontab
