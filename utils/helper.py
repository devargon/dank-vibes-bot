import asyncio
import io
import os
import random
from io import BytesIO
from urllib import parse

import aiohttp
import filetype

import discord
import datetime
from typing import Union, Tuple, Optional

import typing
from discord.ext import menus
from dotenv import load_dotenv
from captcha.image import ImageCaptcha
import functools

load_dotenv('credentials.env')

class BaseEmbed(discord.Embed):
    def __init__(self, color: Union[discord.Color, int] = 0xffcccb, timestamp: datetime.datetime = None,
                 fields: Tuple[Tuple[str, str]] = (), field_inline: Optional[bool] = False, **kwargs):
        super().__init__(color=color, timestamp=timestamp or discord.utils.utcnow(), **kwargs)
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)

    @classmethod
    def default(cls, ctx, **kwargs):
        instance = cls(**kwargs)
        instance.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        return instance

    @classmethod
    def to_error(cls, title: Optional[str] = "Error",
                color: Union[discord.Color, int] = discord.Color.red(), **kwargs):
        return cls(title=title, color=color, **kwargs)


def pages(per_page=1, show_page=True):
    """Compact ListPageSource that was originally made teru but was modified"""
    def page_source(coro):
        async def create_page_header(self, menu, entry):
            result = await discord.utils.maybe_coroutine(coro, self, menu, entry)
            return menu.generate_page(result, self._max_pages)
        def __init__(self, list_pages):
            super(self.__class__, self).__init__(list_pages, per_page=per_page)
        kwargs = {
            '__init__': __init__,
            'format_page': (coro, create_page_header)[show_page]
        }
        return type(coro.__name__, (menus.ListPageSource,), kwargs)
    return page_source

@pages()
def empty_page_format(_, __, entry):
    """This is for Code Block ListPageSource and for help Cog ListPageSource"""
    return entry

def unpack(li):
    for item in li:
        if isinstance(item, list):
            yield from unpack(item)
        else:
            yield item

def generate_random_hash():
    hash = random.getrandbits(128)

    return("%032x" % hash)

async def upload_file_to_bunnycdn(file: typing.Union[str, bytes, os.PathLike, io.BufferedIOBase], filename: str = None, directory: str = None, storage_zone_name="nogra"):
    """Uploads a file to a BunnyCDN Storage Zone."""
    if isinstance(file, io.IOBase):
        if not (file.seekable() and file.readable()):
            raise ValueError(f"File buffer {file!r} must be seekable and readable")
        file_data = file
    elif isinstance(file, (str, os.PathLike)):
        with open(file, "rb") as fp:
            file_data = fp.read()
    else:
        file_data = file
    if filename is None:
        if isinstance(fp, str):
            _, filename = os.path.split(fp)
        else:
            filename = getattr(fp, "name", None)
    else:
        filename = filename
    mime_type = filetype.guess_mime(file_data)
    if mime_type is None:
        mime_type = "application/octet-stream"
    headers = {
        "Content-Type": mime_type,
        "AccessKey": os.getenv('bunnystoragecredentials')
    }
    base_url = f"https://storage.bunnycdn.com/{storage_zone_name}/"
    commercial_base_url = f"https://cdn.nogra.xyz/"
    if directory is not None and directory != "":
        if directory[0] == "/":
            directory = directory[1:]
        if directory[-1] == "/":
            directory = directory[:-1]
        directory += f"/{filename}"
        url = base_url + parse.quote(directory)
        commercial_url = commercial_base_url + parse.quote(directory)
    else:
        url = base_url + parse.quote(filename)
        commercial_url = commercial_base_url + parse.quote(filename)


    async with aiohttp.ClientSession() as session:
        async with session.put(url, data=file_data, headers=headers) as resp:
            resp.raise_for_status()
        return commercial_url, resp.status

async def paste(text: str):
    base_url = "https://paste.nogra.xyz"
    upload_url = f"{base_url}/documents"
    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, data=text.encode("utf-8")) as resp:
            resp.raise_for_status()
            key = await resp.json()
            key = key.get('key', None)
            return f"{base_url}/{key}"



async def generate_captcha():
    """Generates a captcha and returns the picture and the captcha text"""
    def generate_captcha_sync():
        result_str = ''.join(random.choice("abcdefgjkmpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ") for i in range(4))
        image = ImageCaptcha(width=280, height=70)
        data = image.generate(result_str)
        bio = BytesIO()
        image.write(result_str, bio)
        bio.seek(0)
        return result_str, bio
    task = functools.partial(generate_captcha_sync)
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, task)
    try:
        captcha_string, bio = await asyncio.wait_for(task, timeout=10)
    except asyncio.TimeoutError:
        return "", None
    else:
        return captcha_string, bio
