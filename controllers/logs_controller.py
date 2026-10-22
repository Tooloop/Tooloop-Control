import os


class Logs(object):
    """Serves log files"""

    LOG_PATH = "/assets/logs"
    LOG_EXTENSIONS = ["txt", "csv", "log", "json"]

    def __init__(self):
        super(Logs, self).__init__()
        self.load_logs()

    def load_logs(self):
        try:
            filenames = os.listdir(self.LOG_PATH)
        except OSError:
            return []

        extensions = {extension.lower() for extension in self.LOG_EXTENSIONS}
        self.logs = [
            filename
            for filename in filenames
            if os.path.isfile(os.path.join(self.LOG_PATH, filename))
            and os.path.splitext(filename)[1][1:].lower() in extensions
        ]
        self.logs.sort(
            key=lambda filename: os.path.getmtime(os.path.join(self.LOG_PATH, filename)),
            reverse=True,
        )

    def get_logs(self):
        self.load_logs()
        return self.logs

    def get_log(self, log):
        if not isinstance(log, str) or log not in self.logs:
            return ""

        with open(os.path.join(self.LOG_PATH, log), "r", encoding="utf-8") as log_file:
            return log_file.read()

    def get_path(self, filename):
        extensions = {extension.lower() for extension in self.LOG_EXTENSIONS}
        if os.path.isfile(os.path.join(self.LOG_PATH, filename)) and os.path.splitext(filename)[1][1:].lower() in extensions:
            return os.path.join(self.LOG_PATH, filename)
        else:
            raise FileNotFoundError
