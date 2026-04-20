# -*- coding: utf-8 -*-
import threading
import csv
import os
import pwd
import datetime
from utils.time_utils import ISO_string_to_local_time
import atexit
import glob
import time
import sys


class Logging(object):

    def __init__(self, app, system):
        # Initialize critical attributes early to ensure they exist even in child processes
        self.timer = None
        self.is_logging = False
        self.csv_file = None

        # Skip full initialization in Flask reloader child processes
        # Only initialize in the main reloader process
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            return

        super(Logging, self).__init__()
        self.app = app
        self.system = system
        self.data_lock = threading.Lock()
        self.INTERVAL = self.app.config.get("LOGGING_INTERVAL", 30)  # seconds
        self.logs_dir = "/assets/logs"
        self.MAX_LOG_AGE = self.app.config.get("LOGGING_MAX_AGE", 604800)  # 7 days in seconds

        self.cleanup_old_files()

        if self.app.config.get("LOGGING_INTERVAL", False):
            self.start_logging()

        atexit.register(self.stop_logging)

    def __del__(self):
        self.stop_logging()

    def start_logging(self):
        if self.is_logging:
            raise Warning(" * Logging already started")

        self.is_logging = True

        self.csv_file = self.create_new_log_file()
        print(" * Start health logging in " + self.csv_file)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)

        # Write the header if the file doesn't exist or is empty
        if not os.path.exists(self.csv_file) or os.path.getsize(self.csv_file) == 0:
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "CPU Usage [%]",
                                "CPU Temperature [°C]", "Memory Usage [%]"])

        os.chown(self.csv_file,
                 pwd.getpwnam("tooloop").pw_uid,
                 pwd.getpwnam("tooloop").pw_gid)

        # Create timer
        self.timer = threading.Timer(self.INTERVAL, self.tick)
        self.timer.daemon = True
        self.timer.start()

    def stop_logging(self):
        self.is_logging = False
        try:
            if self.timer:
                print(" * Stop health logging")
                self.timer.cancel()
        except Exception as e:
            print(e)

    def create_new_log_file(self):
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"health-monitoring_{current_date}.csv"
        return os.path.join(self.logs_dir, filename)

    def tick(self):
        if not self.is_logging:
            self.stop_logging()
            return

        with self.data_lock:
            cpu_data = self.system.get_cpu()
            memory_data = self.system.get_memory()
            row = [
                ISO_string_to_local_time(cpu_data['timestamp']),
                cpu_data['usage_percent']['cpu'],
                cpu_data['temperature'],
                memory_data['usage_percent']
            ]

            # Write to CSV
            with open(self.csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(row)

            # Set the next timeout to happen
            self.timer = threading.Timer(self.INTERVAL, self.tick, ())
            self.timer.start()

    def cleanup_old_files(self):
        files = glob.glob(os.path.join(
            self.logs_dir, 'health-monitoring_*.csv'))
        for file in files:
            # Check if the file is older than MAX_LOG_AGE days and delete it
            if time.time() - os.path.getctime(file) > self.MAX_LOG_AGE:
                os.remove(file)
