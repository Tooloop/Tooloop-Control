# -*- coding: utf-8 -*-
from subprocess import check_output, check_call, Popen, PIPE, call
import os
import pwd
import time
import fcntl
import glob
import re
import struct
import threading
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

WDIOC_GETSUPPORT = 0x80285700
WDIOC_SETOPTIONS = 0x80045704
WDIOC_SETTIMEOUT = 0xC0045706
WDIOF_MAGICCLOSE = 0x0100
WDIOS_DISABLECARD = 0x0001


class System(object):
    """Holds information of the tooloop box."""

    def __init__(self, app):
        super(System, self).__init__()
        self.app = app
        self.cpu_load = CpuLoad()
        self.needs_reboot = False
        self.runtime_schedule = None
        self.runtime_schedule_path = self.app.root_path+'/data/runtime-schedule.json'
        self.watchdog_lock = threading.Lock()
        self.watchdog_fd = None
        self.watchdog_healthy = None
        self.watchdog_module_loaded_by_app = False

        # read runtime schedule from disk
        try:
            with open(self.runtime_schedule_path) as json_data:
                self.runtime_schedule = json.load(json_data)
        except Exception as e:
            self.runtime_schedule = {
                'startup': {
                    'enabled': False,
                    'weekdays': [1, 2, 3, 4, 5],
                    'time': {
                        'hours': 8,
                        'minutes': 0
                    }
                },
                'shutdown': {
                    'enabled': False,
                    'type': 'poweroff',
                    'weekdays': [1, 2, 3, 4, 5],
                    'time': {
                        'hours': 20,
                        'minutes': 0
                    }
                }
            }

        self.setup_runtime_schedule()
        sensors.init()

    def __exit__(self, exc_type, exc_value, traceback):
        sensors.cleanup()

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

    def is_watchdog_enabled(self):
        with self.watchdog_lock:
            return self.watchdog_fd is not None

    def is_watchdog_configured(self):
        return bool(self.app.config.get('WATCHDOG_ENABLED', False))

    def _get_runtime_watchdog_usec(self):
        output = check_output([
            'systemctl', 'show', '--property=RuntimeWatchdogUSec', '--value'
        ]).decode().strip()
        return int(output)

    def _watchdog_device(self):
        configured_device = self.app.config.get('WATCHDOG_DEVICE', '/dev/watchdog')
        if os.path.exists(configured_device):
            return configured_device
        if configured_device == '/dev/watchdog':
            devices = sorted(glob.glob('/dev/watchdog[0-9]*'))
            if devices:
                return devices[0]
        raise RuntimeError(
            'Hardware watchdog device {} was not found; ensure its kernel driver '
            'is loaded and the device node exists'.format(configured_device))

    def _watchdog_module(self):
        module = self.app.config.get('WATCHDOG_MODULE', 'iTCO_wdt')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', module):
            raise ValueError('Invalid watchdog kernel module name')
        return module

    def _load_watchdog_module(self):
        module = self._watchdog_module()
        module_path = '/sys/module/{}'.format(module.replace('-', '_'))
        if os.path.exists(module_path):
            return
        check_call(['modprobe', module])
        self.watchdog_module_loaded_by_app = True

    def _unload_watchdog_module(self):
        if not self.watchdog_module_loaded_by_app:
            return
        try:
            check_call(['modprobe', '-r', self._watchdog_module()])
            self.watchdog_module_loaded_by_app = False
        except Exception:
            self.app.logger.exception('Could not unload the hardware watchdog module')

    def _persist_watchdog_enabled(self, enabled):
        config_path = os.path.join(self.app.root_path, 'data', 'config.cfg')
        with open(config_path, 'r') as config_file:
            lines = config_file.readlines()

        setting = 'WATCHDOG_ENABLED={}\n'.format(enabled)
        updated = False
        for index, line in enumerate(lines):
            if line.startswith('WATCHDOG_ENABLED='):
                lines[index] = setting
                updated = True
                break
        if not updated:
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'
            lines.append(setting)

        with open(config_path, 'w') as config_file:
            config_file.writelines(lines)
        os.chown(config_path,
                 pwd.getpwnam('tooloop').pw_uid,
                 pwd.getpwnam('tooloop').pw_gid)
        self.app.config['WATCHDOG_ENABLED'] = enabled

    def _configure_watchdog(self, fd):
        timeout = int(self.app.config.get('WATCHDOG_TIMEOUT', 60))
        if timeout <= 0:
            raise ValueError('Watchdog timeout must be a positive number of seconds')

        timeout_buffer = bytearray(struct.pack('i', timeout))
        fcntl.ioctl(fd, WDIOC_SETTIMEOUT, timeout_buffer, True)
        actual_timeout = struct.unpack('i', timeout_buffer)[0]
        if actual_timeout != timeout:
            raise RuntimeError(
                'Hardware watchdog set timeout to {} seconds, not {} seconds'.format(
                    actual_timeout, timeout))

    def _deactivate_watchdog(self, fd):
        disable_buffer = bytearray(struct.pack('i', WDIOS_DISABLECARD))
        try:
            fcntl.ioctl(fd, WDIOC_SETOPTIONS, disable_buffer, True)
        except OSError:
            support = bytearray(40)
            fcntl.ioctl(fd, WDIOC_GETSUPPORT, support, True)
            options = struct.unpack_from('I', support)[0]
            if not options & WDIOF_MAGICCLOSE:
                raise RuntimeError('This hardware watchdog cannot be safely disabled')
            os.write(fd, b'V')
        os.close(fd)

    def _activate_watchdog_locked(self):
        if self.watchdog_fd is not None:
            return
        if self._get_runtime_watchdog_usec() > 0:
            raise RuntimeError(
                'systemd RuntimeWatchdogSec is active; it must be disabled '
                'so only the kiosk health route feeds the hardware watchdog')

        module_was_loaded_by_app = self.watchdog_module_loaded_by_app
        self._load_watchdog_module()
        try:
            fd = os.open(self._watchdog_device(), os.O_WRONLY | os.O_CLOEXEC)
        except Exception:
            if not module_was_loaded_by_app:
                self._unload_watchdog_module()
            raise

        try:
            self._configure_watchdog(fd)
        except Exception as error:
            try:
                self._deactivate_watchdog(fd)
            except Exception as disable_error:
                self.watchdog_fd = fd
                self.watchdog_healthy = None
                self.app.logger.exception('Could not safely deactivate the hardware watchdog')
                raise RuntimeError(
                    'Watchdog setup failed and the device may still be active: {}'.format(
                        disable_error)) from error
            if not module_was_loaded_by_app:
                self._unload_watchdog_module()
            raise

        self.watchdog_fd = fd
        self.watchdog_healthy = None

    def set_watchdog_enabled(self, enabled, persist=True):
        if type(enabled) is not bool:
            raise ValueError('Watchdog enabled state must be a boolean')

        with self.watchdog_lock:
            if enabled:
                self._activate_watchdog_locked()
                try:
                    if persist:
                        self._persist_watchdog_enabled(True)
                except Exception:
                    try:
                        self._stop_watchdog_session_locked()
                    except Exception:
                        self.app.logger.exception('Could not stop watchdog after config persistence failed')
                    raise
                return True

            if self.watchdog_fd is None:
                if persist:
                    self._persist_watchdog_enabled(False)
                return False

            fd = self.watchdog_fd
            if persist:
                self._persist_watchdog_enabled(False)
            try:
                self._stop_watchdog_session_locked()
            except Exception:
                if persist:
                    try:
                        self._persist_watchdog_enabled(True)
                    except Exception:
                        self.app.logger.exception('Could not restore the persisted watchdog state')
                raise
            return False

    def _stop_watchdog_session_locked(self):
        if self.watchdog_fd is None:
            return
        fd = self.watchdog_fd
        self._deactivate_watchdog(fd)
        self.watchdog_fd = None
        self.watchdog_healthy = None
        self._unload_watchdog_module()

    def stop_watchdog_session(self):
        with self.watchdog_lock:
            self._stop_watchdog_session_locked()

    def reset_watchdog(self, healthy=True):
        if type(healthy) is not bool:
            raise ValueError('Kiosk health state must be a boolean')

        with self.watchdog_lock:
            self.watchdog_healthy = healthy
            if not healthy:
                return False
            if self.watchdog_fd is None:
                if not self.is_watchdog_configured():
                    raise RuntimeError('Hardware watchdog is not enabled in configuration')
                self._activate_watchdog_locked()
            os.write(self.watchdog_fd, b'\0')
            return True

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
        # update data
        self.set_single_schedule('startup', schedule)
        self.set_single_schedule('shutdown', schedule)
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

    def set_single_schedule(self, which, schedule):

        if which in schedule:
            if 'enabled' in schedule[which]:
                self.runtime_schedule[which]['enabled'] = schedule[which]['enabled']
            if 'type' in schedule[which]:
                if schedule[which]['type'] in ['blackout', 'poweroff']:
                    self.runtime_schedule[which]['type'] = schedule[which]['type']
            if 'weekdays' in schedule[which]:
                self.runtime_schedule[which]['weekdays'] = schedule[which]['weekdays']
            if 'time' in schedule[which]:
                if 'hours' in schedule[which]['time']:
                    self.runtime_schedule[which]['time']['hours'] = int(
                        schedule[which]['time']['hours'])
                if 'minutes' in schedule[which]['time']:
                    self.runtime_schedule[which]['time']['minutes'] = int(
                        schedule[which]['time']['minutes'])

    def setup_runtime_schedule(self):
        crontab = CronTab(user='tooloop')

        # empty wakealarm
        call('echo 0 > /sys/class/rtc/rtc0/wakealarm', shell=True)

        # remove cron jobs
        crontab.remove_all(command='display-on')
        crontab.remove_all(command='poweroff')
        crontab.remove_all(command='blackout')
        crontab.write()

        # start up
        if self.runtime_schedule['startup']['enabled'] and len(self.runtime_schedule['startup']['weekdays']) > 0:
            if self.runtime_schedule['shutdown']['type'] == 'poweroff':
                # set rtc wake alarm
                call('echo '+str(self.get_next_startup_time()) +
                     ' > /sys/class/rtc/rtc0/wakealarm', shell=True)
            elif self.runtime_schedule['shutdown']['type'] == 'blackout':
                # set startup cron job
                job = crontab.new(
                    command='env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-display-on && env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-presentation-reset')
                job.hour.on(self.runtime_schedule['startup']['time']['hours'])
                job.minute.on(
                    self.runtime_schedule['startup']['time']['minutes'])
                job.dow.on(*self.runtime_schedule['startup']['weekdays'])
                crontab.write()

        # shutdown
        if self.runtime_schedule['shutdown']['enabled'] and len(self.runtime_schedule['shutdown']['weekdays']) > 0:
            if self.runtime_schedule['shutdown']['type'] == 'poweroff':
                job = crontab.new(command='sudo poweroff')
            elif self.runtime_schedule['shutdown']['type'] == 'blackout':
                job = crontab.new(
                    command='env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-blackout')
            job.hour.on(self.runtime_schedule['shutdown']['time']['hours'])
            job.minute.on(self.runtime_schedule['shutdown']['time']['minutes'])
            job.dow.on(*self.runtime_schedule['shutdown']['weekdays'])
            crontab.write()

    def get_next_startup_time(self):
        # What weeday is today?
        weekday = get_iso_weekday()

        # What’s the next weekday to start up?
        next_weekday = min(self.runtime_schedule['startup']['weekdays'])
        for day in sorted(self.runtime_schedule['startup']['weekdays']):
            if day > weekday:
                next_weekday = day
                break

        # Create a date of today at start up time
        next_startup = datetime.datetime.today().replace(
            hour=self.runtime_schedule['startup']['time']['hours'],
            minute=self.runtime_schedule['startup']['time']['minutes'],
            second=0,
            microsecond=0
        )

        # If it is after the daily startup time,
        # add the days between today and the next startup day
        now = datetime.datetime.now().time()
        startup_time = datetime.time(
            hour=self.runtime_schedule['startup']['time']['hours'],
            minute=self.runtime_schedule['startup']['time']['minutes']
        )
        if now > startup_time:
            delta_days = ((next_weekday + 7) - weekday) % 7
            next_startup += datetime.timedelta(days=delta_days)

        # Convert time to unix epoch time (in time utils)
        return datetime_to_unix_time_millis(next_startup)
