import discord
from discord.ext import commands, menus
from colorthief import ColorThief
from utils import checks
from io import BytesIO
from utils.menus import CustomMenu
from typing import Union
import re
from utils import http
from PIL import UnidentifiedImageError

regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #normal urls
        r'localhost|)' #localhoar
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class ColorDisplay(menus.ListPageSource):
    def __init__(self, entries, title, avatar):
        self.title = title
        self.avatar = avatar
        super().__init__(entries, per_page=1)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, description=entries[0], color = entries[2], timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=entries[1])
        embed.set_image(url=self.avatar)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

class color(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="color", aliases=["colour"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def color(self, ctx, argument:Union[discord.Member, str] = None):
        """
        Gets dominant and matching colors of your profile picture.
        """
        if argument is None:
            argument = ctx.author
            image = await ctx.author.display_avatar.with_format('png').read()
        elif isinstance(argument, discord.Member):
            image = await argument.display_avatar.with_format('png').read()
        elif isinstance(argument, str):
            if not regex.match(argument):
                await ctx.send("You provided an invalid image URL.")
                return
            image = await http.get(argument, res_method="read")
        else:
            return await ctx.send('uhm')
        try:
            color_thief = ColorThief(BytesIO(image))
        except UnidentifiedImageError:
            return await ctx.send("I could not read the image provided.")
        palette = color_thief.get_palette(color_count=6)
        messagecontents = []
        for color in palette:
            hexcode = rgb_to_hex(color)
            hex_int = int(hexcode, 16)
            hex_int = hex_int + 0x200
            messagecontents.append((f"HEX: `{hexcode}`\nRGB: `{color}`\nINT: `{int(hex_int)}`", f"https://api.alexflipnote.dev/color/image/{hexcode}", int(hex_int)))
        title = f"{argument.name}'s Profile Picture Color" if isinstance(argument, discord.Member) else "Image dominant colors"
        pages = CustomMenu(source=ColorDisplay(messagecontents, title, argument.display_avatar.url if isinstance(argument, discord.Member) else argument), clear_reactions_after=True, timeout=60)
        return await pages.start(ctx)