# -*- coding: utf-8 -*-
from subprocess import check_output, check_call, Popen, PIPE, call
import os
import pwd
import time
from flask import jsonify
import pexpect
import json
import datetime
from pytz import common_timezones
from utils.time_utils import *
from utils.cpu_load import CpuLoad
from crontab import CronTab
import configparser
import sensors
import atexit
import threading


class System(object):
    """Holds information of the tooloop box."""

    def __init__(self, app):
        super(System, self).__init__()
        print("System controller initialized")
        self.app = app
        self.cpu_load = CpuLoad()
        self.needs_reboot = False
        self.runtime_schedule = None
        self.runtime_schedule_path = self.app.root_path+'/data/runtime-schedule.json'

        # read runtime schedule from disk
        try:
            with open(self.runtime_schedule_path) as json_data:
                schedule = json.load(json_data)
                self.validate_schedule(schedule)
                self.runtime_schedule = schedule
        except Exception as e:
            self.runtime_schedule = {
                'enabled': False,
                'schedule': [
                    {'num': 1, 'name': "Mo", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}},
                    {'num': 2, 'name': "Tu", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}},
                    {'num': 3, 'name': "We", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}},
                    {'num': 4, 'name': "Th", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}},
                    {'num': 5, 'name': "Fr", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}},
                    {'num': 6, 'name': "Sa", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}},
                    {'num': 0, 'name': "Su", 'startup': False, 'startupTime': {
                        'hours': 10, 'minutes': 0}, 'shutdown': False, 'shutdownTime': {'hours': 17, 'minutes': 0}}
                ]
            }

        self.setup_runtime_schedule()

        # Start a separate thread to periodically check the next startup time
        self.schedule_thread_running = True
        self.schedule_thread = threading.Thread(
            target=self.check_next_startup_time)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()

        sensors.init()

        # Register the setup_runtime_schedule function to be called at program exit
        atexit.register(self.cleanup)

    def cleanup(self):
        sensors.cleanup()
        self.setup_runtime_schedule()
        try:
            self.schedule_thread_running = False
            self.schedule_thread.join(timeout=5)
            if self.schedule_thread.is_alive():
                raise RuntimeError("Failed to stop the schedule thread")
        except RuntimeError as e:
            print(f"Error stopping the schedule thread: {e}")

    def get_hostname(self):
        try:
            file = open("/etc/hostname", "r")
            hostname = file.read().rstrip()
            return hostname
        except Exception as e:
            raise

    def set_hostname(self, hostname):
        old_hostname = self.get_hostname()

        # nothing to do
        if hostname == old_hostname:
            return

        # change /etc/hostname
        try:
            file = open("/etc/hostname", "w")
            file.write(hostname)
            file.close()
        except Exception as e:
            raise

        # change /etc/hosts
        try:
            with open('/etc/hosts', 'r') as file:
                filedata = file.read()

            # Replace the target string
            filedata = filedata.replace(old_hostname, hostname)

            # Write the file out again
            with open('/etc/hosts', 'w') as file:
                file.write(filedata)
        except Exception as e:
            raise e

        # Help Chromium start after changing hostname
        # https://issues.chromium.org/issues/41103620
        call('rm -rf /home/tooloop/snap/chromium/common/chromium/Singleton*', shell=True)

        self.needs_reboot = True

    def get_ip(self):
        try:
            return check_output(['hostname', '-I']).decode().rstrip('\n').split()[0]
        except IndexError as e:
            return ''
        except Exception as e:
            raise

    def get_uptime(self):
        uptime_string = check_output(['uptime', '-s']).decode().rstrip('\n')
        return uptime_string

    def get_timezone(self):
        timedate_info = check_output(
            ['timedatectl', 'show']).decode().rstrip('\n')
        config = configparser.ConfigParser()
        config.read_string('[TimeDateInfo]\n' + timedate_info)
        return config['TimeDateInfo']['Timezone']

    def set_timezone(self, timezone):
        # nothing to do
        if timezone == self.get_timezone():
            return jsonify({'timezone': timezone})

        # change timezone
        try:
            os.popen('timedatectl set-timezone ' + timezone)
            return jsonify({'timezone': timezone})
        except Exception as e:
            raise

    def get_available_timezones(self):
        return common_timezones

    def get_hd(self):
        # get hd information
        # /dev/root        7541056 2210616   4994300  31% /

        hd_info = os.popen('df -B1 | grep assets').readline()
        # if no /assets partition is available, get the whole disk
        if hd_info == '':
            hd_info = os.popen('df -B1 | pcregrep -M "/\n"').readline()

        # split string in tokens
        # ['/dev/root', '7541056', '2210616', '4994300', '31%', '/']
        size = int(hd_info.split()[1])

        # assets directoryuptime_string
        packages = int(
            os.popen('du -s -B1 /assets/packages').readline().split()[0])
        data = int(os.popen('du -s -B1 /assets/data').readline().split()[0])
        logs = int(os.popen('du -s -B1 /assets/logs').readline().split()[0])
        presentation = int(
            os.popen('du -s -B1 /assets/presentation').readline().split()[0])
        screenshots = int(
            os.popen('du -s -B1 /assets/screenshots').readline().split()[0])

        return {
            'unit': 'Byte',
            'size': size,
            'data': data,
            'logs': logs,
            'packages': packages,
            'presentation': presentation,
            'screenshots': screenshots
        }

    def get_cpu(self):

        temperature = 0
        max_temperature = 0
        crit_temperature = 0

        for chip in sensors.ChipIterator():  # optional arg like "coretemp-*" restricts iterator
            # Check if the chip has "temp" in it’s name
            # example for an AMD CPU: k10temp-pci-00c3
            # example for an Intel CPU: coretemp-isa-0000
            if "temp" in sensors.chip_snprintf_name(chip):
                for feature in sensors.FeatureIterator(chip):
                    if feature.type != sensors.feature.TEMP:
                        continue

                    sub_features = list(sensors.SubFeatureIterator(
                        chip, feature))  # get a list of all subfeatures

                    # Some subfeatures can't be read
                    try:
                        for sub_feature in sub_features:
                            name = sub_feature.name.decode("utf-8")
                            if name == "temp1_input":
                                temperature = sensors.get_value(
                                    chip, sub_feature.number)
                            elif name == "temp1_max":
                                max_temperature = sensors.get_value(
                                    chip, sub_feature.number)
                            elif name == "temp1_crit":
                                crit_temperature = sensors.get_value(
                                    chip, sub_feature.number)
                    except:
                        return

        usage = self.cpu_load.get_cpu_load()
        return {
            'timestamp': time_to_ISO_string(time.gmtime()),
            'temperature': temperature,
            'maxTemperature': max_temperature,
            'criticalTemperature': temperature,
            'usage_percent': usage
        }

    def get_gpu(self):
        # temperature = os.popen('vcgencmd measure_temp').readline()
        # temperature = float(temperature.lstrip('temp=').rstrip("'C\n"))
        # return {
        #     'timestamp': time_to_ISO_string(time.gmtime()),
        #     'temperature': temperature
        # }
        return {
            'timestamp': time_to_ISO_string(time.gmtime()),
            'temperature': 0
        }

    def get_memory(self):
        with open('/proc/meminfo', 'r') as mem:
            tmp = 0
            for i in mem:
                sline = i.split()
                if str(sline[0]) == 'MemTotal:':
                    total = int(sline[1])
                elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                    tmp += int(sline[1])
        total = total / 1024
        free = tmp / 1024
        used = total - free
        usage_percent = (float(used) * 100) / float(total)
        return {
            'timestamp': time_to_ISO_string(time.gmtime()),
            'unit': 'MB',
            'total': total,
            'free': free,
            'used': used,
            'usage_percent': usage_percent
        }

    def reboot(self):
        try:
            check_call(["reboot"])
        except Exception as e:
            raise

    def poweroff(self):
        try:
            check_call(["poweroff"])
        except Exception as e:
            raise

    def set_password(self, old_password, new_password):
        child = pexpect.spawn(
            '/usr/bin/sudo -u tooloop /usr/bin/passwd tooloop')
        try:
            # Prompt for old password
            i = child.expect(
                ['[Oo]ld [Pp]assword', '[Cc]urrent password', '[Nn]ew [Pp]assword'])

            # Type old password
            if i == 0 or i == 1:
                child.sendline(old_password)
                child.expect('[Nn]ew [Pp]assword')

            # Type new password
            child.sendline(new_password)

            # Prompt to retype new password
            i = child.expect(
                ['[Nn]ew [Pp]assword', '[Rr]etype', '[Rr]e-enter'])
            if i == 0:
                message = child.before
                print('Host did not like new password. Here is what it said...')
                print(message)
                child.send(chr(3))  # Ctrl-C
                # This should tell remote passwd command to quit.
                child.sendline('')
                raise Exception(message)

            # Retype new pasword
            child.sendline(new_password)
            child.expect('[$#] ')
            print(child.after)

        except pexpect.TIMEOUT:
            return child.before.decode().lstrip(': \r\n').rstrip('\r\n')
        except pexpect.EOF:
            return child.before.decode().lstrip(': \r\n').rstrip('\r\n')

    def to_dict(self):
        return {
            'needs_reboot': self.needs_reboot,
            'hostname': self.get_hostname()
        }

    def get_audio_volume(self):
        try:
            output = check_output(
                'su tooloop -c "pactl --server=/run/user/1000/pulse/native list sinks"', shell=True).decode().split('\n')
            for line in output:
                # find the output lint with the volume
                if 'Volume' in line and not 'Base' in line:
                    # find the first channels’ volume as we are ignoring separate channels
                    tokens = line.split()
                    for token in tokens:
                        if '%' in token:
                            return int(token.rstrip('%'))
        except Exception as e:
            return 0

    def set_audio_volume(self, volume):
        call('su tooloop -c "pactl --server=/run/user/1000/pulse/native set-sink-volume 0 ' +
             str(volume)+'%"', shell=True)

    def set_audio_mute(self, mute):
        mute_param = '1' if mute else '0'
        call('su tooloop -c "pactl --server=/run/user/1000/pulse/native set-sink-mute 0 ' +
             mute_param+'"', shell=True)

    def get_audio_mute(self):
        try:
            for line in check_output('su tooloop -c "pactl --server=/run/user/1000/pulse/native list sinks"', shell=True).decode().split('\n'):
                if 'Mute' in line:
                    return 'yes' in line
        except Exception as e:
            raise

    def get_display_state(self):
        # check result
        ps = Popen('xset q | grep Monitor', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        try:
            state = output.split()[-1].decode()
        except IndexError as e:
            state = 'unknown'
        return state

    def set_display_state(self, state):
        if not state.lower() in ['on', 'off', 'standby']:
            raise ValueError(
                "Display state can only be one of 'on', 'off' or 'standby'")
        call(['xset', 'dpms', 'force', state.lower()])
        return self.get_display_state()

    def get_runtime_schedule(self):
        return self.runtime_schedule

    def set_runtime_schedule(self, schedule):
        try:
            self.validate_schedule(schedule)
        except Exception as e:
            raise e

        # Update the runtime schedule
        self.runtime_schedule = schedule

        # write changes to disk
        try:
            with open(self.runtime_schedule_path, 'w') as json_file:
                json.dump(self.runtime_schedule, json_file, indent=4)

            os.chown(self.runtime_schedule_path,
                     pwd.getpwnam("tooloop").pw_uid,
                     pwd.getpwnam("tooloop").pw_gid)
        except Exception as e:
            raise e

        # set up the rtc wakealarm and cron jobs
        self.setup_runtime_schedule()

    def validate_schedule(self, schedule):
        if not isinstance(schedule, dict):
            raise ValueError("Schedule must be a dictionary")

        if 'enabled' not in schedule or not isinstance(schedule['enabled'], bool):
            raise ValueError("Schedule must contain a boolean 'enabled' field")

        if 'schedule' not in schedule or not isinstance(schedule['schedule'], list):
            raise ValueError("Schedule must contain a 'schedule' list")

        for day_schedule in schedule['schedule']:
            if not isinstance(day_schedule, dict):
                raise ValueError("Each day in schedule must be a dictionary")

            required_fields = ['num', 'name', 'startup',
                               'startupTime', 'shutdown', 'shutdownTime']
            for field in required_fields:
                if field not in day_schedule:
                    raise ValueError(
                        f"Each day must contain a '{field}' field")

            if not isinstance(day_schedule['num'], int) or day_schedule['num'] < 0 or day_schedule['num'] > 6:
                raise ValueError(
                    "Day number must be an integer between 0 and 6")

            if not isinstance(day_schedule['name'], str) or len(day_schedule['name']) != 2:
                raise ValueError("Day name must be a 2-character string")

            if not isinstance(day_schedule['startup'], bool):
                raise ValueError("Startup must be a boolean")

            if not isinstance(day_schedule['startupTime'], dict):
                raise ValueError("Startup time must be a dictionary")

            if 'hours' not in day_schedule['startupTime'] or 'minutes' not in day_schedule['startupTime']:
                raise ValueError(
                    "Startup time must contain 'hours' and 'minutes' fields")

            if not isinstance(day_schedule['startupTime']['hours'], int) or day_schedule['startupTime']['hours'] < 0 or day_schedule['startupTime']['hours'] > 23:
                raise ValueError(
                    "Startup hours must be an integer between 0 and 23")

            if not isinstance(day_schedule['startupTime']['minutes'], int) or day_schedule['startupTime']['minutes'] < 0 or day_schedule['startupTime']['minutes'] > 59:
                raise ValueError(
                    "Startup minutes must be an integer between 0 and 59")

            if not isinstance(day_schedule['shutdown'], bool):
                raise ValueError("Shutdown must be a boolean")

            if not isinstance(day_schedule['shutdownTime'], dict):
                raise ValueError("Shutdown time must be a dictionary")

            if 'hours' not in day_schedule['shutdownTime'] or 'minutes' not in day_schedule['shutdownTime']:
                raise ValueError(
                    "Shutdown time must contain 'hours' and 'minutes' fields")

            if not isinstance(day_schedule['shutdownTime']['hours'], int) or day_schedule['shutdownTime']['hours'] < 0 or day_schedule['shutdownTime']['hours'] > 23:
                raise ValueError(
                    "Shutdown hours must be an integer between 0 and 23")

            if not isinstance(day_schedule['shutdownTime']['minutes'], int) or day_schedule['shutdownTime']['minutes'] < 0 or day_schedule['shutdownTime']['minutes'] > 59:
                raise ValueError(
                    "Shutdown minutes must be an integer between 0 and 59")

    def check_next_startup_time(self):
        while self.schedule_thread_running:
            next_startup_time = self.get_next_startup_time()
            if next_startup_time:
                current_time = datetime_to_unix_time_millis(
                    datetime.datetime.now())
                if current_time >= next_startup_time:
                    self.setup_runtime_schedule()
            time.sleep(60)  # Check every minute

    def setup_runtime_schedule(self):
        crontab = CronTab(user='tooloop')

        # empty wakealarm
        call('echo 0 > /sys/class/rtc/rtc0/wakealarm', shell=True)

        # remove poweroff cron job
        crontab.remove_all(command='poweroff')
        crontab.write()

        # return early if schedule is disabled
        if 'enabled' not in self.runtime_schedule or not isinstance(self.runtime_schedule['enabled'], bool):
            return

        # set new start up wakealarm
        next_startup_time = self.get_next_startup_time()
        print('next_startup_time', next_startup_time)

        if next_startup_time:
            # set rtc wake alarm
            call('echo '+str(next_startup_time) +
                 ' > /sys/class/rtc/rtc0/wakealarm', shell=True)

        # set shutdown cron job
        # if self.runtime_schedule['shutdown']['enabled'] and len(self.runtime_schedule['shutdown']['weekdays']) > 0:
        #     if self.runtime_schedule['shutdown']['type'] == 'poweroff':
        #         job = crontab.new(command='sudo poweroff')
        #     elif self.runtime_schedule['shutdown']['type'] == 'blackout':
        #         job = crontab.new(
        #             command='env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-blackout')
        #     job.hour.on(self.runtime_schedule['shutdown']['time']['hours'])
        #     job.minute.on(self.runtime_schedule['shutdown']['time']['minutes'])
        #     job.dow.on(*self.runtime_schedule['shutdown']['weekdays'])
        #     crontab.write()

    def get_next_startup_time(self):
        # Get all days with scheduled start up
        startup_days = [
            day for day in self.runtime_schedule['schedule'] if day['startup']]

        # Return if there are none
        if not startup_days:
            return

        # What’s the next weekday to start up?
        today = get_iso_weekday()
        next_startup_day = None

        # Find the next startup day after today
        for day in sorted(startup_days, key=lambda x: x['num']):
            if day['num'] > today:
                next_startup_day = day
                break

        # If no startup day found after today, get the first one (next week)
        if not next_startup_day:
            next_startup_day = min(startup_days, key=lambda x: x['num'])

        # Calculate the next start up time
        next_startup = datetime.datetime.now()
        next_startup = next_startup.replace(hour=next_startup_day['startupTime']['hours'],
                                            minute=next_startup_day['startupTime']['minutes'],
                                            second=0, microsecond=0)

        # If the next startup day is today but the time has already passed, set it to next week
        if next_startup_day['num'] == today and next_startup < datetime.datetime.now():
            next_startup += datetime.timedelta(days=7)

        # If the next startup day is before today, set it to next week
        elif next_startup_day['num'] < today:
            next_startup += datetime.timedelta(
                days=7 - (today - next_startup_day['num']))

        # If the next startup day is after today, set it to the next occurrence of that day
        elif next_startup_day['num'] > today:
            next_startup += datetime.timedelta(
                days=next_startup_day['num'] - today)

        print('next_startup', next_startup)

        return datetime_to_unix_time_millis(next_startup)
