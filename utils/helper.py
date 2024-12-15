import datetime
from typing import Union, Tuple, Optional

import aiohttp
import discord
from discord.ext import menus
from dotenv import load_dotenv

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


async def paste(text: str):
    base_url = "https://paste.nogra.xyz"
    upload_url = f"{base_url}/documents"
    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, data=text.encode("utf-8")) as resp:
            resp.raise_for_status()
            key = await resp.json()
            key = key.get('key', None)
            return f"{base_url}/{key}"
