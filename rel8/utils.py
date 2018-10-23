#!/usr/bin/env python3
import datetime
from flask_login import current_user
import pytz
from pytz import timezone


def get_local_dt(dt, human=False, format='%b %-d, %Y, %-I:%M %p'):
    tz = timezone(current_user.timezone)
    utc = timezone('UTC')
    dt = utc.localize(dt, is_dst=None).astimezone(pytz.utc)
    local_dt = dt.astimezone(tz)

    if human:
        return local_dt.strftime(format)
    return local_dt
