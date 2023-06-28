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
/opt/tooloop/control-center/venv/bin/pip install Flask pexpect python-crontab zeroconf

# publish services over Avahi/Bonjour
cat > /etc/avahi/services/tooloop-control-center.service <<EOF
<?xml version="1.0" standalone='no'?>
<!--*-nxml-*-->
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">%h</name>
  <service>
    <type>_tooloop-control-center._tcp</type>
    <port>80</port>
  </service>
</service-group>
EOF
