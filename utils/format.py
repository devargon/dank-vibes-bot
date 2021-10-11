import sys
import discord
import traceback
from io import BytesIO
from typing import Sequence, Iterator
from discord.ext import commands
import inflect
import math
from expr import evaluate

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

def short_time(duration:int):
    if duration is None or duration < 1:
        return ''
    duration_in_mins = duration/60
    if duration_in_mins < 1:
        return '< 1m'
    if duration_in_mins < 60:
        return f'{math.ceil(duration_in_mins)}m'
    duration_in_hours = duration_in_mins/60
    if duration_in_hours < 1.017:
        return '1h'
    if duration_in_hours < 24:
        return f'{math.ceil(duration_in_hours)}h'
    duration_in_days = duration_in_hours/24
    if duration_in_days < 1.05:
        return '1d'
    else:
        return f'{math.ceil(duration_in_days)}d'



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
    p = inflect.engine()
    return p.ordinal(number)

def get_command_name(command: commands.command):
    """
    Returns commands name.
    """
    if command.parent:
        return f"{command.parent} {command.name}"
    return f"{command.name}"

class TabularData:
    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def render(self):
        """
        Renders a table in rST format.
        """

        sep = '+'.join('-' * w for w in self._widths)
        sep = f'+{sep}+'

        to_draw = [sep]

        def get_entry(d):
            elem = '|'.join(f'{e:^{self._widths[i]}}' for i, e in enumerate(d))
            return f'|{elem}|'

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return '\n'.join(to_draw)

def stringnum_toint(string:str):
    allowedsymbols=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "m", "k", 'e', '.', '-']
    string = string.lower()
    for character in list(string):
        if character not in allowedsymbols:
            return None
    if string.isnumeric():
        return int(string)
    if "m" in string:
        string = string.replace("m", "*1000000+")
    if "k" in string:
        string = string.replace("d", "*1000+")
    if 'e' in string:
        string = string.replace("e", "*10^")
    if string.endswith('+') or string.endswith('-'):
        string += "0"
    if string.endswith('/') or string.endswith('*') or string.endswith('^'):
        string += "1"
    intstring = evaluate(string)
    intstring = int(intstring) if intstring is not None else intstring
    return intstring