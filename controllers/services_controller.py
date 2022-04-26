# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE, call
import fileinput
from crontab import CronTab


class Services(object):
    """Holds information of the running services."""

    def __init__(self, app):
        super(Services, self).__init__()
        self.app = app

    def is_vnc_running(self):
        ps = Popen('systemctl --machine=tooloop@.host --user status x11vnc | grep "active (running)"',
                   shell=True, stdout=PIPE)
        output = ps.stdout.read().decode()
        ps.stdout.close()
        ps.wait()
        return output != ""

    def enable_vnc(self):
        call('systemctl --machine=tooloop@.host --user enable x11vnc', shell=True)
        call('systemctl --machine=tooloop@.host --user start x11vnc', shell=True)

    def disable_vnc(self):
        call('systemctl --machine=tooloop@.host --user stop x11vnc', shell=True)
        call('systemctl --machine=tooloop@.host --user disable x11vnc', shell=True)

    def is_ssh_running(self):
        ps = Popen('systemctl status ssh | grep "active (running)"',
                   shell=True, stdout=PIPE)
        output = ps.stdout.read().decode()
        ps.stdout.close()
        ps.wait()
        return output != ""

    def enable_ssh(self):
        call('systemctl enable ssh', shell=True)
        call('systemctl start ssh', shell=True)

    def disable_ssh(self):
        call('systemctl stop ssh', shell=True)
        call('systemctl disable ssh', shell=True)

    def is_control_center_running(self):
        return self.app.config['HOST'] == '0.0.0.0'

    def enable_control_center(self):
        # change server config
        with fileinput.input(self.app.root_path+"/data/config.cfg", inplace=True) as file:
            for line in file:
                new_line = line.replace('127.0.0.1', '0.0.0.0')
                print(new_line, end='')
        call('systemctl restart tooloop-control', shell=True)

    def disable_control_center(self):
        # change server config
        with fileinput.input(self.app.root_path+"/data/config.cfg", inplace=True) as file:
            for line in file:
                new_line = line.replace('0.0.0.0', '127.0.0.1')
                print(new_line, end='')
        call('systemctl restart tooloop-control', shell=True)

    def is_screenshot_service_running(self):
        crontab = CronTab(user='tooloop')
        for job in crontab:
            if job.command == 'env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-screenshot' and job.is_enabled():
                return True
        return False

    def enable_screenshot_service(self):
        crontab = CronTab(user='tooloop')
        for job in crontab:
            if job.command == 'env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-screenshot' and not job.is_enabled():
                job.enable()
        crontab.write()

    def disable_screenshot_service(self):
        crontab = CronTab(user='tooloop')
        for job in crontab:
            if job.command == 'env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-screenshot' and job.is_enabled():
                job.enable(False)
        crontab.write()

    def get_status(self):
        return {
            'vnc': self.is_vnc_running(),
            'ssh': self.is_ssh_running(),
            'control_center': self.is_control_center_running(),
            'screenshot_service': self.is_screenshot_service_running()
        }
