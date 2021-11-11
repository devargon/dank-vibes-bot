import discord
from discord.ext import commands, menus
from colorthief import ColorThief
from utils import checks
from io import BytesIO
from utils.menus import CustomMenu

class ColorDisplay(menus.ListPageSource):
    def __init__(self, entries, title, avatar):
        self.title = title
        self.avatar = avatar
        super().__init__(entries, per_page=1)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, description=entries[0], color = 0x57F0F0, timestamp=discord.utils.utcnow())
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
    async def color(self, ctx, member: discord.Member = None):
        """
        Gets dominant and matching colors of your profile picture.
        """
        if member is None:
            member = ctx.author
        avatar = await member.display_avatar.with_format('png').read()
        color_thief = ColorThief(BytesIO(avatar))
        palette = color_thief.get_palette(color_count=6)
        messagecontents = []
        for color in palette:
            hexcode = rgb_to_hex(color)
            hex_int = int(hexcode, 16)
            hex_int = hex_int + 0x200
            messagecontents.append((f"HEX: `{hexcode}`\nRGB: `{color}`\nINT: `{int(hex_int)}`", f"https://api.alexflipnote.dev/color/image/{hexcode}"))
        title = f"{member.name}'s Profile Picture Color"
        pages = CustomMenu(source=ColorDisplay(messagecontents, title, member.display_avatar.url), clear_reactions_after=True, timeout=60)
        return await pages.start(ctx)