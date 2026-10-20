# Tooloop-Control

![](https://img.shields.io/github/license/tooloop/tooloop-control.svg)

A browser based settings app for [Tooloop OS](https://github.com/Tooloop/Tooloop-OS).

![control-center](https://github.com/Tooloop/Tooloop-Control/assets/4962676/d27a5a6f-5970-457b-aab5-646ba3bea7c4)


# Installation


## Clone repository

    git clone --recursive https://github.com/Tooloop/Tooloop-Control.git


## Create a Python environment

    python3 -m venv venv
    . venv/bin/activate


## Install flask and dependencies

    pip install --upgrade pip
    pip install Flask pexpect python-crontab 


## Run development

    sudo ./venv/bin/python app.py


# Development

## Watch and compile SASS files

    sass --watch --style compressed static/css/styles.scss:static/css/styles.css


# Production


## Install server

Create directory

    sudo mkdir /opt/tooloop/control-center
    sudo chown tooloop:tooloop /opt/tooloop/control-center

Install as described above


## Create system service

Copy `.service` to

    /usr/lib/systemd/system/tooloop-control.service

Enable

    sudo systemctl enable tooloop-control

Start

    sudo systemctl start tooloop-control


## Hardware watchdog

The System page enables the native hardware watchdog. The enabled state is
stored in `data/config.cfg`; the timeout defaults to 60 seconds. This setting is
a persistent permission, not an active timer. The device stays closed when the
Control Center starts. `PUT /tooloop/api/v1.0/system/watchdog` with
`{"enabled": true}` explicitly opens it; alternatively, the first healthy reset
request opens it implicitly when the setting is enabled. Use
`POST /tooloop/api/v1.0/system/watchdog/reset` with `{"healthy": true}` every
20 seconds. A false health result does not feed the timer; a missing heartbeat
also lets it expire. `GET` on the same reset URL is supported as a healthy
heartbeat for clients that use the simpler request.

Stopping the presentation closes the active watchdog session while preserving
the setting, so a later healthy heartbeat can start a new session. Disabling
the setting closes the session and persists the disabled state.

The Control Center opens the Linux watchdog device and keeps it open. The
device defaults to `/dev/watchdog` and falls back to `/dev/watchdog0`; a
different path can be set with `WATCHDOG_DEVICE`. Activation is refused while
systemd `RuntimeWatchdogSec` is active, so there is only one timer owner. A
kernel module is loaded with `modprobe` when the switch is enabled. The default
module is `iTCO_wdt`; set `WATCHDOG_MODULE` for a different board. 
On deactivation, the module is removed only when this process loaded it, and 
only after the watchdog was successfully disabled. Drivers with `nowayout` may 
prevent deactivation. Keep the API on a trusted network.
The kiosk client should only send the heartbeat after confirming that its
presentation loop is responsive.
