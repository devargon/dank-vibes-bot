import copy
import math

import discord
from discord.ext import commands
from thefuzz import process

from utils import checks

import imghdr
import aiohttp
from typing import Union
from emoji import UNICODE_EMOJI
from utils.context import DVVTcontext
import re

from utils.buttons import confirm
from utils.converters import BetterColor, BetterBetterRoles
from utils.format import generate_loadbar
from utils.time import humanize_timedelta

regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #normal urls
        r'localhost|)' #localhoar
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def get_info(role: discord.Role) -> discord.Embed:
    description = [
        f"{role.mention}",
        f"Members: {len(role.members)} | Position: {role.position}",
        f"Color: {role.color}",
        f"Hoisted: {role.hoist}",
        f"Mentionable: {role.mentionable}",
    ]
    if role.managed:
        description.append(f"Managed: {role.managed}")
    e = discord.Embed(
        color=role.color,
        title=role.name,
        description="\n".join(description),
        timestamp=role.created_at,
    )
    e.set_footer(text=role.id)
    return e


role_names = {
    847881491426050148: "Highest Donator Role",
    914387371150176297: "Amari Weekly Winner 1",
    939756363859521576: "Amari Weekly Winner 2",
    922382151574487070: "Amari Weekly Winner 3",
    666514218434166794: "Contest Winner 1",
    908360574545567754: "Contest Winner 2",
    831954125675429958: "Weekly Dank Winner 1",
    935057118493540352: "Weekly Dank Winner 2",
    677839284211810333: "Weekly Dank Winner 3",
    931218082163220510: "Grinder T2 Custom Role",
    931215261950943263: "Top Grinder Custom Role",
    902413229609857024: "Top Karuta Donor 1",
    947749191386542100: "Top Karuta Donor 2",
    936084400221851668: "Karuta Donor Custom Role (GW)"
}


class Role(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="role", invoke_without_command=True)
    async def role_cmd(self, ctx, member: discord.Member = None, *, role: BetterBetterRoles):
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
    async def role_icon(self, ctx, role: BetterBetterRoles = None, argument: Union[discord.Emoji, discord.PartialEmoji, str] = None):
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
    @role_cmd.command(name="name", aliases=["setname", "n"])
    async def role_name(self, ctx: DVVTcontext, role: BetterBetterRoles, *, new_name: str):
        role: discord.Role = role
        failembed = discord.Embed(title="Role Edit Failed", color=discord.Color.red())
        if not ctx.me.guild_permissions.manage_roles:
            failembed.description = "I don't have permission to edit any roles. Please allow me the `Manage Roles` permission in your server's Role settings."
            return await ctx.send(embed=failembed)
        if ctx.me.top_role is not None and role > ctx.me.top_role:
            failembed.description = "I don't have permission to edit this role as it is above my highest role."
            return await ctx.send(embed=failembed)
        if len(new_name) > 100:
            failembed.description = "The new name of the role cannot be longer than **100 characters**.\nYour provided name is **{}** characters long.".format(len(new_name))
            return await ctx.send(embed=failembed)
        else:
            old_name = role.name
            try:
                newrole = await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", name=new_name)
            except discord.Forbidden as e:
                failembed.description = str(e)
                return await ctx.send(embed=failembed)
            except Exception as e:
                failembed.description = f"An unexpected error occured: {e}"
                return await ctx.send(embed=failembed)
            else:
                content = f"<:DVB_True:887589686808309791> The name of **{old_name}** has been set to **{newrole.name}**."

                await ctx.send(content, embed=get_info(newrole))

    @checks.has_permissions_or_role(manage_roles=True)
    @role_cmd.command(name="color", aliases=["colour"])
    async def role_color(self, ctx: DVVTcontext, role: BetterBetterRoles, color: BetterColor):
        role: discord.Role = role
        if color is None:
            return await ctx.send("Please provide a valid color in the format of:\n`#FFFFFF`\n`FFFFFF`\n`0xFFFFFF`\n`0x#FFFFFF`\n`rgb(255, 255, 255)`\nA colour name")
        failembed = discord.Embed(title="Role Edit Failed", color=discord.Color.red())
        if not ctx.me.guild_permissions.manage_roles:
            failembed.description = "I don't have permission to edit any roles. Please allow me the `Manage Roles` permission in your server's Role settings."
            return await ctx.send(embed=failembed)
        if ctx.me.top_role is not None and role > ctx.me.top_role:
            failembed.description = "I don't have permission to edit this role as it is above my highest role."
            return await ctx.send(embed=failembed)
        else:
            old_color = ((hex(role.color.value))[2:]).zfill(6)
            try:
                newrole = await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", color=color)
            except discord.Forbidden as e:
                failembed.description = str(e)
                return await ctx.send(embed=failembed)
            except Exception as e:
                failembed.description = f"An unexpected error occured: {e}"
                return await ctx.send(embed=failembed)
            else:
                content = f"<:DVB_True:887589686808309791> **{role.name}**'s color has been changed from **#{old_color}** to **#{((hex(color.value))[2:]).zfill(6)}**."
                await ctx.send(content, embed=get_info(newrole))


    @checks.has_permissions_or_role(manage_roles=True)
    @role_cmd.command(name="reset", aliases=["r"])
    async def role_reset(self, ctx: DVVTcontext, role: BetterBetterRoles):
        role: discord.Role = role
        failembed = discord.Embed(title="Role Reset Failed", color=discord.Color.red())
        if not ctx.me.guild_permissions.manage_roles:
            failembed.description = "I don't have permission to edit any roles. Please allow me the `Manage Roles` permission in your server's Role settings."
            return await ctx.send(embed=failembed)
        if ctx.me.top_role is not None and role > ctx.me.top_role:
            failembed.description = "I don't have permission to edit this role as it is above my highest role."
            return await ctx.send(embed=failembed)
        else:
            role_name = role_names.get(role.id, None)
            if role_name is None:
                failembed.description = "This role is not recorded as a role that requires a reset.\nContact the developer if you think this is wrong."
                return await ctx.send(embed=failembed)
            else:
                try:
                    newrole = await role.edit(reason=f"Requested by {ctx.author} ({ctx.author.id})", name=role_name, color=0)
                except discord.Forbidden as e:
                    failembed.description = str(e)
                    return await ctx.send(embed=failembed)
                except Exception as e:
                    failembed.description = f"An unexpected error occured: {e}"
                    return await ctx.send(embed=failembed)
                else:
                    content = f"<:DVB_True:887589686808309791> **{role.name}** has been reset."
                    await ctx.send(content, embed=get_info(newrole))
                    existing = await self.client.db.fetchrow("SELECT * FROM customroles WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id)
                    if existing is not None:
                        c1 = confirm(ctx, self.client, 30.0)
                        c1.response = await ctx.send("This role is a custom role owned by some users. Would you like to reset its custom role status?", view=c1)
                        await c1.wait()
                        if c1.returning_value is True:
                            message = copy.copy(ctx.message)
                            message.channel = ctx.channel
                            message.content = ctx.prefix + "crole remove " + role.mention
                            new_ctx = await self.client.get_context(message, cls=type(ctx))
                            await self.client.invoke(new_ctx)






    @checks.has_permissions_or_role(manage_roles=True)
    @role_cmd.command(name="removeall", aliases=['rall'])
    async def role_removeall(self, ctx, *, role: BetterBetterRoles = None):
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
