# Tooloop-Control

![](https://img.shields.io/badge/status-in%20development-red.svg)
![](https://img.shields.io/github/license/tooloop/tooloop-control.svg)

A browser based settings Control Center for Tooloop OS.
It’s a re-write of the old [Tooloop Settings Server](https://github.com/Tooloop/Tooloop-Settings-Server). It’s supposed to replace it in the effort of moving Tooloop OS to Ubuntu 22.04.


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

    sudo python3 app.py


# Development

## Watch and compile SASS files

    sass --watch --style compressed static/css/styles.scss static/css/styles.css


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