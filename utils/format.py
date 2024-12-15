import sys
import traceback
from io import BytesIO
from typing import Sequence, Iterator, Optional, Union

import discord
import inflect
from discord.ext import commands
from expr import evaluate

from utils.errors import ArgumentBaseError

p = inflect.engine()


class plural:
    """
    Auto corrects text to show plural or singular depending on the size number.
    """
    def __init__(self, value):
        self.value = value
    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'
        if abs(v) != 1:
            return f'{v} {plural}'
        return f'{v} {singular}'

def comma_number(number:int):
    return "{:,}".format(number)



def proper_userf(user: Union[discord.Member, discord.User], show_at_symbol: Optional[bool] = True):
    if user.discriminator is not None:
        if user.discriminator.isnumeric and int(user.discriminator) > 0:
            return f"{user.name}#{user.discriminator}"
        else:
            return f"@{user.name}" if show_at_symbol else f"{user.name}"
    else:
        return f"@{user.name}" if show_at_symbol else f"{user.name}"


def human_join(seq, delim=', ', final='or'):
    """
    Returns a str with <final> before the last word.
    """
    size = len(seq)
    if size == 0:
        return ''
    if size == 1:
        return seq[0]
    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'
    return delim.join(seq[:-1]) + f' {final} {seq[-1]}'

def escape(text: str, *, mass_mentions: bool = False, formatting: bool = False) -> str:
    """
    Get text with all mass mentions or markdown escaped.
    """
    if mass_mentions:
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
    if formatting:
        text = discord.utils.escape_markdown(text)
    return text

def text_to_file(text: str, filename: str = "file.txt", encoding: str = "utf-8"):
    """
    Prepares text to be sent as a file on Discord, without character limit.
    """

    file = BytesIO(text.encode(encoding))
    return discord.File(file, filename)

def box(text: str, lang: str = "") -> str:
    """
    Returns the given text inside a codeblock.
    """
    ret = "```{}\n{}\n```".format(lang, text)
    return ret

def inline(text: str) -> str:
    """
    Returns the given text as inline code.
    """
    if "`" in text:
        return "``{}``".format(text)
    else:
        return "`{}`".format(text)

def pagify(text: str, delims: Sequence[str] = ["\n"], *, priority: bool = False, escape_mass_mentions: bool = True, shorten_by: int = 8, page_length: int = 2000, box_lang: str = None) -> Iterator[str]:
    """
    Generate multiple pages from the given text.
    """
    in_text = text
    page_length -= shorten_by
    while len(in_text) > page_length:
        this_page_len = page_length
        if escape_mass_mentions:
            this_page_len -= in_text.count("@here", 0, page_length) + in_text.count(
                "@everyone", 0, page_length
            )
        closest_delim = (in_text.rfind(d, 1, this_page_len) for d in delims)
        if priority:
            closest_delim = next((x for x in closest_delim if x > 0), -1)
        else:
            closest_delim = max(closest_delim)
        closest_delim = closest_delim if closest_delim != -1 else this_page_len
        if escape_mass_mentions:
            to_send = escape(in_text[:closest_delim], mass_mentions=True)
        else:
            to_send = in_text[:closest_delim]
        if len(to_send.strip()) > 0:
            to_send = box(to_send, lang=box_lang) if box_lang is not None else to_send
            yield to_send
        in_text = in_text[closest_delim:]

    if len(in_text.strip()) > 0:
        in_text = box(in_text, lang=box_lang) if box_lang is not None else in_text
        if escape_mass_mentions:
            yield escape(in_text, mass_mentions=True)
        else:
            yield in_text

def print_exception(text, error):
    """
    Prints the exception with proper traceback.
    """
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    etype = type(error)
    trace = error.__traceback__
    lines = traceback.format_exception(etype, error, trace)
    return ''.join(lines)

def ordinal(number:int):
    return p.ordinal(number)

def plural_noun(noun: str):
    return p.plural_noun(noun)


def get_command_name(command: Union[commands.Command, discord.ApplicationCommand]):
    """
    Returns commands name.
    """
    if isinstance(command, commands.Command):
        if command.parent:
            return f"{get_command_name(command.parent)} {command.name}"
        else:
            return command.name
    elif isinstance(command, discord.ApplicationCommand):
        return command.qualified_name

def stringnum_toint(string:str):
    allowedsymbols = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "m", "k", 'e', '.', '-', ',']
    string = string.lower()
    for character in list(string):
        if character not in allowedsymbols:
            return None
    if string.isnumeric():
        return int(string)
    if "," in string:
        string = string.replace(", ", "").replace(",", "")
    if "m" in string:
        string = string.replace("m", "*1000000+")
    if "k" in string:
        string = string.replace("k", "*1000+")
    if 'e' in string:
        string = string.replace("e", "*10^")
    if string.endswith('+') or string.endswith('-'):
        string += "0"
    if string.endswith('/') or string.endswith('*') or string.endswith('^'):
        string += "1"
    try:
        intstring = evaluate(string)
    except:
        raise ArgumentBaseError(message=f"Something went wrong while I was trying to calculate how much you meant from `{string}`. Please contact the developer about this!")
    intstring = int(intstring) if intstring is not None else intstring
    return intstring


def stringtime_duration(string:str):
    allowedsymbols=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "m", "s", 'h', 'y', 'd', 'r', 'e', 'c', 'm', 'i', 'n', 'w', 'k']
    string = string.lower()
    for character in list(string):
        if character not in allowedsymbols:
            return None
    if string.isnumeric():
        return int(string)
    if 'sec' in string:
        string = string.replace('sec', '+')
    if 's' in string:
        string = string.replace('s', '+')
    if 'min' in string:
        string = string.replace('mins', '*60+').replace('min', '*60+')
    if 'm' in string:
        string = string.replace('m', '*60+')
    if 'hour' in string:
        string = string.replace('hours', '*3600+').replace('hour', '*3600+')
    if 'hr' in string:
        string = string.replace('hrs', '*3600+').replace('hr', '*3600+')
    if 'h' in string:
        string = string.replace('h', '*3600+')
    if 'day' in string:
        string = string.replace('days', '*86400+').replace('day', '*86400+')
    if 'd' in string:
        string = string.replace('d', '*86400+')
    if 'week' in string:
        string = string.replace('weeks', '*604800+').replace('week', '*604800+')
    if 'w' in string:
        string = string.replace('w', '*604800+')
    if 'year' in string:
        string = string.replace('years', '*31536000+').replace('year', '*31536000+')
    if 'yr' in string:
        string = string.replace('yrs', '*31536000+').replace('yr', '*31536000+')
    if 'y' in string:
        string = string.replace('y', '*31536000+')
    if string.endswith('+') or string.endswith('-'):
        string += "0"
    if string.endswith('/') or string.endswith('*') or string.endswith('^'):
        string += "1"
    try:
        intstring = evaluate(string)
    except:
        return None
    intstring = int(intstring) if intstring is not None else intstring
    return intstring

def generate_loadbar(percentage: float, length: Optional[int] = 20):
    aStartLoad = "<a:DVB_aStartLoad:912007459898544198>"
    aMiddleLoad = "<a:DVB_aMiddleLoad:912007457214185565>"
    aEndLoad = "<a:DVB_aEndLoad:912007457591668827>"
    StartLoad = "<:DVB_StartLoad:912007458581516289>"
    MiddleLoad = "<:DVB_MiddleLoad:912007459118411786>"
    EndLoad = "<:DVB_EndLoad:912007458594127923>"
    eStartLoad = "<:DVB_eStartLoad:912007458938044436>"
    eMiddleLoad = "<:DVB_eMiddleLoad:912007458992574534>"
    eEndLoad = "<:DVB_eEndLoad:912007458942230608>"
    if length is None:
        length = 20
    rounded = round(percentage * length)
    if rounded == 0:
        return eStartLoad + eMiddleLoad * (length - 2) + eEndLoad
    else:
        if rounded == length:
            return StartLoad + MiddleLoad * (length - 2) + aEndLoad
        else:
            if rounded > 1:
                return StartLoad + MiddleLoad * (rounded - 1 - 1) + aMiddleLoad  + eMiddleLoad * (length - rounded - 1) + eEndLoad
            else:
                return aStartLoad + eMiddleLoad * (length - 1 - 1) + eEndLoad