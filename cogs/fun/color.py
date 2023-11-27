import discord
from discord.ext import commands, menus, pages
from colorthief import ColorThief
from utils import checks
from io import BytesIO
from utils.menus import CustomMenu
from typing import Union
import re
from utils import http
from PIL import UnidentifiedImageError
from utils.converters import BetterColor

regex = re.compile(
        r'^https?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))' #localhoar # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class SetRoleColor(discord.ui.View):
    def __init__(self, client, ctx):
        self.client = client
        self.ctx = ctx
        self.success_set_color = None
        super().__init__()

    @discord.ui.button(label=f"Set this as your custom role color", emoji="🎨")
    async def set_role_color(self, button: discord.ui.Button, interaction: discord.Interaction):
        color = interaction.message.embeds[0].color
        if color is None:
            color = discord.Color(0)
        failembed = discord.Embed(title="Role Edit Failed", color=discord.Color.red())
        users_role = await self.client.db.fetchval("SELECT role_id FROM customroles WHERE guild_id = $1 AND user_id = $2", interaction.guild.id, interaction.user.id)
        if self.success_set_color == color:
            failembed.description = "You already changed your custom role to this color!"
            return await interaction.response.send_message(embed=failembed, ephemeral=True)
        if users_role is None:
            failembed.description = "You do not own a custom role."
            return await interaction.response.send_message(embed=failembed, ephemeral=True)
        role = interaction.guild.get_role(users_role)
        if role is None:
            failembed.description = "You do not own a custom role."
            return await interaction.response.send_message(embed=failembed, ephemeral=True)
        if role >= self.ctx.me.top_role:
            failembed.description = "⚠️ **This role is higher than my highest role.** I cannot edit the color."
            return await interaction.response.send_message(embed=failembed, ephemeral=True)
        old_color = ((hex(role.color.value))[2:]).zfill(6)
        try:
            await role.edit(color=color, reason=f"Requested by role owner {interaction.user} ({interaction.user.id})")
        except discord.Forbidden as e:
            failembed.description = str(e)
            return await interaction.response.send_message(embed=failembed, ephemeral=True)
        except Exception as e:
            failembed.description = f"An unexpected error occured: {e}"
            return await interaction.response.send_message(embed=failembed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Role Edit Successful",
                description=f"Your custom role, **{role.name}**'s color has been changed from **#{old_color}** to **#{((hex(color.value))[2:]).zfill(6)}**.",
                color=discord.Color.green()
            )
            embed.set_footer(text="What? You think I'm going to call you wonderful like Yui! In your dreams!")
            self.success_set_color = color
            return await interaction.response.send_message(interaction.user.mention, embed=embed)





def format_pages(entries, avatar, title):
    pages = []
    for i in entries:
        embed = discord.Embed(title=title, description=i[0], color=i[2])
        embed.set_thumbnail(url=i[1])
        embed.set_image(url=avatar)
        pages.append(embed)
    return pages

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

class color(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="color", aliases=["colour"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def color(self, ctx, argument: Union[discord.Member, discord.Color, str] = None):
        """
        Gets dominant and matching colors of your profile picture. You can also specify another member, a color or an image link.
        """
        if argument is None:
            argument = ctx.author
            image = await ctx.author.display_avatar.with_format('png').read()
        elif isinstance(argument, discord.Member):
            image = await argument.display_avatar.with_format('png').read()
        elif isinstance(argument, discord.Colour):
            image = argument
        elif isinstance(argument, str):
            if len(argument) == 6:
                try:
                    argument = await commands.ColorConverter().convert(ctx, f"#{argument}")
                except Exception as e:
                    if not regex.match(argument):
                        await ctx.send("You provided an invalid image URL or color.")
                        return
                    image = await http.get(argument, res_method="read")
                else:
                    image = argument
            else:
                if not regex.match(argument):
                    await ctx.send("You provided an invalid image URL or color.")
                    return
                image = await http.get(argument, res_method="read")
        else:
            return await ctx.send('uhm')
        if isinstance(image, discord.Colour):
            color = image.to_rgb()
            hexcode = rgb_to_hex(color)
            hex_int = int(hexcode, 16)
            messagecontents = (f"HEX: `{hexcode}`\nRGB: `{color}`\nINT: `{int(hex_int)}`", f"https://argon-alexflipnote-api.herokuapp.com/color?color={hexcode}", hex_int)
        else:
            try:
                color_thief = ColorThief(BytesIO(image))
            except UnidentifiedImageError:
                return await ctx.send("I could not read the image provided.")
            palette = color_thief.get_palette(color_count=6)
            messagecontents = []
            for color in palette:
                hexcode = rgb_to_hex(color)
                hex_int = int(hexcode, 16)
                messagecontents.append((f"HEX: `{hexcode}`\nRGB: `{color}`\nINT: `{int(hex_int)}`", f"https://argon-alexflipnote-api.herokuapp.com/color?color={hexcode}", int(hex_int)))
        title = f"{argument.name}'s Profile Picture Color" if isinstance(argument, discord.Member) else "Your Color" if isinstance(argument, discord.Color) else "Image dominant colors"
        raw_entries = [messagecontents] if type(messagecontents) == tuple else messagecontents
        embed_pages = format_pages(raw_entries, argument.display_avatar.url if isinstance(argument, discord.Member) else f"https://argon-alexflipnote-api.herokuapp.com/color?color={hexcode}?size=1000" if isinstance(argument, discord.Colour) else argument if isinstance(argument, str) else None, title)
        if (users_role := await self.client.db.fetchval("SELECT role_id FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)) is not None:
            paginator = pages.Paginator(embed_pages, show_disabled=True, custom_view=SetRoleColor(self.client, ctx))
        else:
            paginator = pages.Paginator(embed_pages, show_disabled=True)
        await paginator.send(ctx)

