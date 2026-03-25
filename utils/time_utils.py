import time
import datetime
from datetime import timezone
# import pytz


def gmtime_from_string(time_string, format_string):
    return time.gmtime(time.mktime(time.strptime(time_string, format_string)))


def time_to_ISO_string(gmtime):
    # ISO 8601 Extended Format
    # YYYY-MM-DDTHH:mm:ss.sssZ
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', gmtime)


def ISO_string_to_local_time(utc_timestamp):
    utc_time = datetime.datetime.strptime(
        utc_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone()

    return local_time.strftime("%Y-%m-%d %H:%M:%S")


def get_iso_weekday():
    return datetime.datetime.today().isoweekday()


def datetime_to_unix_time_millis(d):
    return int(d.strftime("%s"))
