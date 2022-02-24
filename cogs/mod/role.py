import math

import discord
from discord.ext import commands
from fuzzywuzzy import process

from utils import checks

import imghdr
import aiohttp
from typing import Union
from emoji import UNICODE_EMOJI
import re

from utils.buttons import confirm
from utils.format import generate_loadbar
from utils.time import humanize_timedelta


class BetterRoles(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.RoleConverter().convert(ctx, argument)
        except commands.BadArgument:
            role_to_return = discord.utils.find(lambda x: x.name.lower() == argument.lower(), ctx.guild.roles)
            if role_to_return is not None:
                return role_to_return
            roles_and_aliases = {}
            for r in ctx.guild.roles:
                roles_and_aliases[r.name] = r.id
                # This might be a bad idea, don't care
            name, ratio = process.extractOne(argument, [x for x in roles_and_aliases])
            if ratio >= 75:
                role_to_return = discord.utils.get(ctx.guild.roles, id=roles_and_aliases[name])
                return role_to_return

regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #normal urls
        r'localhost|)' #localhoar
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class Role(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="role", invoke_without_command=True)
    async def role_cmd(self, ctx, member: discord.Member = None, *, role: BetterRoles = None):
        """
        Use this command to add or remove a role to a user.
        """
        if member is None:
            return await ctx.send("You need to specify a member to add a role.")
        if role is None:
            return await ctx.send(f"You need to specify a role to add to {member}.")
        if not role.is_assignable():
            return await ctx.send(
                f"You cannot add **{role.name}** to **{member}**; this may be as the role is an integration, the role of another bot, guild default roles (like `@everyone`, Booster role), or that the role is higher than my highest role.")
        if role >= ctx.author.top_role:
            return await ctx.send(
                f"You cannot add **{role.name}** to **{member}** as the role is higher than or the same as your own highest role.")
        if role in member.roles:
            try:
                await member.remove_roles(role, reason=f"Requested by {ctx.author} ({ctx.author.id})")
            except discord.Forbidden:
                return await ctx.send(f"I don't have permission to remove **{role.name}** from **{member}**.")
            await ctx.send(f"Removed **{role.name}** from **{member}**.")
        else:
            try:
                await member.add_roles(role, reason=f"Requested by {ctx.author} ({ctx.author.id})")
            except discord.Forbidden:
                return await ctx.send(f"I don't have permission to add **{role.name}** to **{member}**.")
            await ctx.send(f"Added **{role.name}** to **{member}**.")

    @checks.has_permissions_or_role(manage_roles=True)
    @role_cmd.command(name='icon')
    async def role_icon(self, ctx, role: BetterRoles = None, argument: Union[discord.Emoji, discord.PartialEmoji, str] = None):
        """
        Changes the icon of a role in the server.
        The supported arguments are an emoji, a image URL, or an attachment.
        The bot will check for the argument in this order:
        `Attachment > Emoji > URL > "None"`
        If `None` is given, the bot will remove the icon instead."""
        if 'ROLE_ICONS' not in ctx.guild.features:
            return await ctx.send("⚠️ **Your server currently does not have the role icon feature.** You require Level 2 Boosts for your server to be able to use role icons.")
        if role is None:
            return await ctx.send("You need to specify a role for which you are editing the role icon.")
        if role >= ctx.me.top_role:
            return await ctx.send(f"I cannot edit the icon of **{role.name}** as the role is higher than or the same as **my** highest role.")
        if role > ctx.author.top_role:
            return await ctx.send("You **cannot** edit a role that is higher than your own highest role.")
        if len(ctx.message.attachments) > 0:
            argumenttype = "ATTACHMENT"
            argument = ctx.message.attachments[0]
        elif isinstance(argument, str):
            if argument in UNICODE_EMOJI['en']:
                argumenttype = "UNICODE"
            elif re.match(regex, argument):
                argumenttype = "URL"
            elif argument.lower() == "none":
                argumenttype = "NONE"
                argument = None
            else:
                return await ctx.send(
                    f"Your argument needs to be of (in order) an Attachment, Custom Emoji, Unicode Emoji or URL. If you are removing the role icon, run `role icon @{role.name} None`.")
        else:
            argumenttype = "EMOJI"
        if argument is None and argumenttype != "NONE":
            return await ctx.send("You need to specify an argument (an entity) to set the role icon to. It can be an Attachment, Custom Emoji, Unicode Emoji, or URL.")
        try:
            if argumenttype == "NONE":
                await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", icon=None)
                successembed = discord.Embed(title="Success!", description=f"The role icon for **{role.name}** has been removed.", color=discord.Color.green())

            elif argumenttype == "UNICODE":
                await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", unicode_emoji=argument)
                successembed = discord.Embed(title="Success!", description=f"The role icon for **{role.name}** has been set to {argument}.", color=discord.Color.green())

            elif argumenttype == "ATTACHMENT":
                if argument.size > 262144:
                    return await ctx.send("The attachment is too big for me to read. The maximum file size of a role icon is 256 KB.")
                imagebytes = await argument.read()
                imagetype = imghdr.what(None, imagebytes)
                if imagetype is None:
                    return await ctx.send("The attachment is not an image.")
                elif imagetype not in ['png', 'jpeg', 'jpg', 'webp']:
                    return await ctx.send("The attachment that you provided cannot be used. Only .PNG, .JPEG and .WEBP files are supported.")
                await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", icon=imagebytes)
                successembed = discord.Embed(title="Success!", description=f"The role icon for **{role.name}** has been set to the provided attachment.", color=discord.Color.green())

            elif argumenttype == "EMOJI":
                imagebytes = await argument.read()
                imagetype = imghdr.what(None, imagebytes)
                if imagetype is None:
                    return await ctx.send("The emoji you provided is not valid.")
                elif imagetype not in ['png', 'jpeg', 'jpg', 'webp']:
                    return await ctx.send("The emoji that you provided cannot be used. Only .PNG, .JPEG and .WEBP files (A.K.A. non-animated emojis) are supported.")
                await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", icon=imagebytes)
                successembed = discord.Embed(title="Success!", description=f"The role icon for **{role.name}** has been set to the requested custom emoji.", color=discord.Color.green())

            elif argumenttype == "URL":
                async with aiohttp.ClientSession() as session:
                    async with session.get(argument) as resp:
                        if resp.status != 200:
                            return await ctx.send("The URL you provided is not valid.")
                        imagebytes = await resp.read()
                imagetype = imghdr.what(None, imagebytes)
                if imagetype is None:
                    return await ctx.send("The URL you provided is not valid.")
                elif imagetype not in ['png', 'jpeg', 'jpg', 'webp']:
                    return await ctx.send("The URL you provided is not a picture that can be used. Only .PNG, .JPEG and .WEBP files are supported.")
                await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", icon=imagebytes)
                successembed = discord.Embed(title="Success!", description=f"The role icon for **{role.name}** has been set to the requested URL.", color=discord.Color.green())
            else:
                successembed = discord.Embed(title="This action failed", description="An unexpected error occured; inform the developer about this.", color=discord.Color.red())
            await ctx.send(embed=successembed)
        except (discord.Forbidden, discord.HTTPException, discord.InvalidArgument) as e:
            if e == discord.Forbidden:
                return await ctx.send(f"I don't have permission to edit the role **{role.name}** :(")
            elif e == discord.HTTPException:
                await ctx.send("An unexpected error occured.\nThis could happen as:\n<:ReplyCont:871807889587707976> The image size is too big (only images smaller than 256 kb is allowed).\n<:Reply:871808167011549244> The image type/format is not supported.\nA report has been sent to the developer to investigate the cause.")
                raise e
            elif e == discord.InvalidArgument:
                return await ctx.send("The role you provided is not valid.")

    @checks.has_permissions_or_role(manage_roles=True)
    @role_cmd.command(name="removeall", aliases=['rall'])
    async def role_removeall(self, ctx, *, role: BetterRoles = None):
        """Removes all members from a role."""
        if role is None:
            return await ctx.send("You need to provide a role.")
        role: discord.Role = role
        if len(role.members) == 0:
            return await ctx.send(f"There is no one with the role **{role.name}**!")
        if len(role.members) < 5:
            approx = 1.0
        else:
            approx = (1.0 +4.8) * (len(role.members)/5)
        approx = round(approx)
        confirmview = confirm(ctx, self.client, 10.0)
        embed = discord.Embed(title="Dangerous action!", description=f"Are you sure you want to **remove** the **{role.name}** role off **{len(role.members)}** members? This process will take approximately **{humanize_timedelta(seconds=approx)}**.", color=discord.Color.orange())
        confirmview.response = await ctx.send(embed=embed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            embed.color, embed.description = discord.Color.red(), "The action has been cancelled."
            return await confirmview.response.edit(embed=embed)
        success = 0
        original_count = len(role.members)
        failed = {}
        split = math.ceil(len(role.members)/10) if len(role.members) > 30 else 5
        def generate_embed():
            embed = discord.Embed(title="Removing roles...", description=f"{success} of {original_count} members processed.", color=discord.Color.green())
            embed.add_field(name="Progress", value=f"{generate_loadbar(percentage=success/original_count, length=10)} {round(success/original_count*100)}%", inline=False)
            return embed
        await confirmview.response.edit(embed=generate_embed())
        for member in role.members:
            try:
                await member.remove_roles(role, reason=f"Requested by {ctx.author} ({ctx.author.id})")
            except Exception as e:
                failed[member] = str(e)
            else:
                success += 1
            if success % split == 0:
                embed = generate_embed()
                await confirmview.response.edit(embed=embed)
        cont = f"<:DVB_True:887589686808309791> **{role.name}** successfully removed from **{success}** members!"
        if len(failed) > 0:
            str_list = []
            for member, error in failed.items():
                str_list.append(f"{member} ({member.id}): {error}")
            embed = discord.Embed(title=f"I couldn't remove the role from {len(failed)} people:", description="\n".join(str_list), color=discord.Color.red())
        else:
            embed = None
        await confirmview.response.edit(embed=generate_embed())
        await ctx.send(cont, embed=embed)
