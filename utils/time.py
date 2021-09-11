import re
import datetime
from typing import Optional, List, SupportsInt
from .format import plural, human_join
from datetime import timedelta
from discord.ext import commands
from dateutil.relativedelta import relativedelta

TIME_RE_STRING = r"\s?".join(
    [
        r"((?P<weeks>\d+?)\s?(weeks?|w))?",                  # e.g. 2w
        r"((?P<days>\d+?)\s?(days?|d))?",                    # e.g. 4d
        r"((?P<hours>\d+?)\s?(hours?|hrs|hr?))?",            # e.g. 10h
        r"((?P<minutes>\d+?)\s?(minutes?|mins?|m(?!o)))?",   # e.g. 20m
        r"((?P<seconds>\d+?)\s?(seconds?|secs?|s))?",        # e.g. 30s
    ]
)

TIME_RE = re.compile(TIME_RE_STRING, re.I)

def parse_timedelta(
    argument: str,
    *,
    maximum: Optional[timedelta] = None,
    minimum: Optional[timedelta] = None,
    allowed_units: Optional[List[str]] = None,
) -> Optional[timedelta]:
    matches = TIME_RE.match(argument)
    allowed_units = allowed_units or ["weeks", "days", "hours", "minutes", "seconds"]
    if matches:
        params = {k: int(v) for k, v in matches.groupdict().items() if v is not None}
        for k in params.keys():
            if k not in allowed_units:
                raise commands.BadArgument(
                    ("`{unit}` is not a valid unit of time for this command").format(unit=k)
                )
        if params:
            delta = timedelta(**params)
            if maximum and maximum < delta:
                raise commands.BadArgument(("This amount of time is too large for this command. (Maximum: {maximum})").format(maximum=humanize_timedelta(timedelta=maximum)))
            if minimum and delta < minimum:
                raise commands.BadArgument(("This amount of time is too small for this command. (Minimum: {minimum})").format(minimum=humanize_timedelta(timedelta=minimum)))
            return delta
    return None

def humanize_timedelta(*, timedelta: Optional[timedelta] = None, seconds: Optional[SupportsInt] = None) -> str:
    try:
        obj = seconds if seconds is not None else timedelta.total_seconds()
    except AttributeError:
        raise ValueError("You must provide either a timedelta or a number of seconds")

    seconds = int(obj)
    periods = [
        (("year"), ("years"), 60 * 60 * 24 * 365),
        (("month"), ("months"), 60 * 60 * 24 * 30),
        (("day"), ("days"), 60 * 60 * 24),
        (("hour"), ("hours"), 60 * 60),
        (("minute"), ("minutes"), 60),
        (("second"), ("seconds"), 1),
    ]

    strings = []
    for period_name, plural_period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value == 0:
                continue
            unit = plural_period_name if period_value > 1 else period_name
            strings.append(f"{period_value} {unit}")

    return human_join(strings, final='and')

def human_timedelta(dt, *, source=None, accuracy=3, brief=False, suffix=True):
    """
    Get locale aware human timedelta representation.
    """
    now = source or discord.utils.utcnow()
    now = now.replace(microsecond=0)
    dt = dt.replace(microsecond=0)
    if dt > now:
        delta = relativedelta(dt, now)
        suffix = ''
    else:
        delta = relativedelta(now, dt)
        suffix = ' ago' if suffix else ''
    attrs = [
        ('year', 'y'),
        ('month', 'mo'),
        ('day', 'd'),
        ('hour', 'h'),
        ('minute', 'm'),
        ('second', 's'),
    ]
    output = []
    for attr, brief_attr in attrs:
        elem = getattr(delta, attr + 's')
        if not elem:
            continue
        if elem <= 0:
            continue
        if brief:
            output.append(f'{elem}{brief_attr}')
        else:
            output.append(format(plural(elem), attr))
    if accuracy is not None:
        output = output[:accuracy]
    if len(output) == 0:
        return 'now'
    else:
        if not brief:
            return human_join(output, final='and') + suffix
        else:
            return ' '.join(output) + suffix