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
