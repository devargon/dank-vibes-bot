import asyncio
import re
import time
import os

import discord
import datetime
from discord.ext import commands
import copy
from utils.buttons import confirm, SingleURLButton
from utils.format import proper_userf
from utils import checks
from main import dvvt
from utils.errors import ArgumentBaseError

DONATOR_25M_ID = 820011992428707840 if os.getenv('state') == '0' else 943883455610109962
LEVEL_30_ID = 944519382577586196 if os.getenv('state') == '0' else 958285021175754793
LEVEL_50_ID = 944519459580821524 if os.getenv('state') == '0' else 943883516565942352
LEVEL_100_ID = 717120742512394323 if os.getenv('state') == '0' else 943883531573157889


class ChannelOrMember(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return await commands.MemberConverter().convert(ctx, argument)
            except:
                return None


class Highlight(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.last_seen = {}
        self.regex_pattern = re.compile('([^\s\w]|_)+')
        self.website_regex = re.compile("https?://[^\s]*")
        self.blacklist = []

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['hl'])
    async def highlight(self, ctx, *, text: str = None):
        """
        Adds a text or phrase to your highlight list.
        When you don't talk after a minute, you will be DMed if someone highlights you with said phrase.
        """
        def get_highlight_limit():
            donator_25 = ctx.guild.get_role(DONATOR_25M_ID)
            level_30 = ctx.guild.get_role(LEVEL_30_ID)
            level_50 = ctx.guild.get_role(LEVEL_50_ID)
            level_100 = ctx.guild.get_role(LEVEL_100_ID)
            hl_limit = 0
            if donator_25 is None:
                raise ArgumentBaseError(message=f"{DONATOR_25M_ID} is not a valid role ID for donator_25")
            elif donator_25 in ctx.author.roles:
                hl_limit += 1
            if level_30 is None:
                raise ArgumentBaseError(message=f"{LEVEL_30_ID} is not a valid role ID for level_30")
            elif level_30 in ctx.author.roles:
                hl_limit += 1
            if level_50 is None:
                raise ArgumentBaseError(message=f"{LEVEL_50_ID} is not a valid role ID for level_50")
            elif level_50 in ctx.author.roles:
                hl_limit += 2
            if level_100 is None:
                raise ArgumentBaseError(message=f"{LEVEL_100_ID} is not a valid role ID for level_100")
            elif level_100 in ctx.author.roles:
                hl_limit += 1000
            return hl_limit
        if text is None:
            return await ctx.send("You need to specify text that you want to be highlighted for.")
        text = (await commands.clean_content().convert(ctx, text)).lower()
        if len(text) < 2:
            return await ctx.send("The text you want to be highlighted for needs to be at least 2 characters long.")
        if len(text) > 50:
            return await ctx.send("The text that you want to be highlighted for can only be 50 characters long.")
        count = await self.client.db.fetchval("SELECT COUNT(*) FROM highlight WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        if count >= get_highlight_limit():
            donator_25 = ctx.guild.get_role(DONATOR_25M_ID)
            level_30 = ctx.guild.get_role(LEVEL_30_ID)
            level_50 = ctx.guild.get_role(LEVEL_50_ID)
            level_100 = ctx.guild.get_role(LEVEL_100_ID)
            desc = []
            if donator_25 not in ctx.author.roles:
                desc.append(f"` - ` You can get `1` highlight by being a **{donator_25.name}**.")
            if level_30 not in ctx.author.roles:
                desc.append(f"` - ` You can get `1` highlight by being **{level_30.name}**.")
            if level_50 not in ctx.author.roles:
                desc.append(f"` - ` You can get `2` highlights by being **{level_50.name}** (Level 50).")
            if level_100 not in ctx.author.roles:
                desc.append(f"` - ` You can get **unlimited** highlights by being **{level_100.name}** (Level 100).")
            actual_description = "\n".join(desc)
            if get_highlight_limit() == 0:
                return await ctx.send(f"You aren't able to get any highlights.\n{actual_description}")
            else:
                return await ctx.send(f"You can only have a maximum of {get_highlight_limit()} highlights.\n{actual_description}")
        exising_hl = await self.client.db.fetchval("SELECT highlights FROM highlight WHERE user_id = $1 AND guild_id = $2 AND highlights = $3", ctx.author.id, ctx.guild.id, text)
        if exising_hl is None:
            await self.client.db.execute("INSERT INTO highlight(guild_id, user_id, highlights) VALUES ($1, $2, $3)", ctx.guild.id, ctx.author.id, text)
            await ctx.send(f"'{text}' has been added to your highlights.")
        else:
            await ctx.send(f"'{text}' is already in your highlights.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @highlight.command(name="block", aliases=['ignore'])
    async def highlight_block(self, ctx, argument: ChannelOrMember = None):
        """
        Adds a member or channel to the highlight block list.
        If a user in this list highlights you, or you were highlighted in a ignored channel, you will not be notified of it.
        """
        if argument is None:
            return await ctx.send("The argument that you need to specify should be a channel or member.")
        hl_blocks = await self.client.db.fetchval("SELECT ignore_id FROM highlight_ignores WHERE user_id = $1 AND guild_id = $2 AND ignore_id = $3", ctx.author.id, ctx.guild.id, argument.id)
        if hl_blocks is None:
            if isinstance(argument, discord.Member):
                await self.client.db.execute("INSERT INTO highlight_ignores(guild_id, user_id, ignore_type, ignore_id) VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, 'member', argument.id)
            elif isinstance(argument, discord.TextChannel):
                await self.client.db.execute("INSERT INTO highlight_ignores(guild_id, user_id, ignore_type, ignore_id) VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, 'channel', argument.id)
            await ctx.send(f"**{argument.name}** has been added to your highlight block list.")
        else:
            await ctx.send(f"**{argument.name}** is already in your highlight block list.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @highlight.command(name="clear", aliases=['reset'], no_pm=True)
    async def highlight_clear(self, ctx):
        """
        Resets your highlight list.
        """
        confirmview = confirm(ctx, self.client, 20.0)
        confirmview.response = await ctx.send("**Are you sure** you want to clear all your highlights? This action **cannot be reversed!**", view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            return await ctx.send("Your highlight list has **not** been reset.")
        else:
            await self.client.db.execute("DELETE FROM highlight WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        await ctx.send("All your highlights have been removed.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @highlight.command(name="remove", aliases=['-'])
    async def highlight_remove(self, ctx, *, text: str):
        """
        Removes a phrase or text from your highlight list.
        """
        text = (await commands.clean_content().convert(ctx, text)).lower()
        if text is None:
            return await ctx.send("You need to specify text that you want to have removed from your highlights.")
        await self.client.db.fetchval("SELECT highlights FROM highlight WHERE user_id = $1 AND guild_id = $2 AND highlights = $3", ctx.author.id, ctx.guild.id, text)
        if text is None:
            return await ctx.send("You aren't tracking this text at all 🤨")
        await self.client.db.execute("DELETE FROM highlight WHERE user_id=$1 AND guild_id=$2 AND highlights=$3", ctx.author.id, ctx.guild.id, text)
        await ctx.send(f"Removed '{text}' from your highlighted words.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @highlight.command(name="show", aliases=['display', 'list'])
    async def highlight_show(self, ctx):
        """
        Shows all the phrases or text that you're tracking, along with any ignored members or channels.
        """
        if ctx.guild is None:
            return
        all_highlights = await self.client.db.fetch("SELECT highlights FROM highlight WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
        if len(all_highlights) == 0:
            hls = "You're not tracking any words yet. Use `highlight add <text>` to start tracking."
        else:
            hls = '\n'.join([highlight.get('highlights') for highlight in all_highlights])
        all_ignores = await self.client.db.fetch("SELECT ignore_id, ignore_type FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
        if len(all_ignores) == 0:
            igns = "None"
        else:
            igsn = []
            for ignore in all_ignores:
                if ignore.get('ignore_type') == 'channel':
                    chan = ctx.guild.get_channel(ignore.get('ignore_id'))
                    if chan is None:
                        obj = f"{ignore.get('ignore_id')} (unknown channel)"
                    else:
                        obj = chan.mention
                else:
                    if (member := ctx.guild.get_member(ignore.get('ignore_id'))) is not None:
                        obj = f"{member.mention} ({proper_userf(member)})"
                    else:
                        obj = f"{ignore.get('ignore_id')} (unknown member)"
                igsn.append(obj)
            igns = '\n'.join(igsn)
        embed = discord.Embed(title="You're currently tracking the following words: ", description=hls, color=self.client.embed_color)
        embed.add_field(name="You're currently ignoring the following channels/members: ", value=igns, inline=False)
        return await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @highlight.command(name="unblock", aliases=['unignore'], no_pm=True)
    async def highlight_unblock(self, ctx, argument: ChannelOrMember = None):
        """
        Removes a channel or member from your highlight ignore list.
        """
        if argument is None:
            return await ctx.send("You need to specify a channel or member to unblock.")
        hl_blocks = await self.client.db.fetchval("SELECT ignore_id FROM highlight_ignores WHERE user_id = $1 AND guild_id = $2 AND ignore_id = $3", ctx.author.id, ctx.guild.id, argument.id)
        if hl_blocks is not None:
            await self.client.db.execute("DELETE FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2 AND ignore_id = $3", ctx.guild.id, ctx.author.id, argument.id)
            await ctx.send(f"**{argument.name}** has been removed from your highlight block list.")
        else:
            await ctx.send(f"**{argument.name}** isn't in your highlight block list.")

    async def generate_context(self, msg, hl):
        fmt = []
        async for m in msg.channel.history(limit=5):
            m.created_at.timestamp()
            msg_content = m.content
            msg_content = msg_content if len(msg_content) < 200 else msg_content[:200] + "..."
            fmt.append(f"**[{time}] {m.author.name}:** {msg_content}")
        e = discord.Embed(title=f"**{hl}**", description='\n'.join(fmt[::-1]), color=0xb47eb3, timestamp=discord.utils.utcnow())
        return e

    @commands.Cog.listener()
    async def on_message(self, message):
        self.last_seen[message.author.id] = round(time.time()) # Logs the user's last seen timing
        if message.guild is None:
            return
        if message.author.bot:
            return
        a = await self.client.db.fetch("SELECT highlights, user_id FROM highlight WHERE guild_id = $1", message.guild.id)
        a = [[hl_entry.get('highlights'), hl_entry.get('user_id')] for hl_entry in a] # gets all the highlights

        final_message = self.website_regex.sub('', message.content.lower())
        final_message = self.regex_pattern.sub('', final_message)
        final_message = [x for x in final_message.split()] # formats the mesasge for better parsing

        notified = []
        for k, v in a:
            local_last_seen = self.last_seen.get(v, self.client.uptime.timestamp())
            if (round(time.time()) - local_last_seen) > 60:
                if k.lower() in final_message and message.author.id != v and v not in notified:
                    # highlight is in nessage, user not notified yet
                    if highlighted_member := message.guild.get_member(v):  # user is in the server
                        if await self.client.check_blacklisted_user(highlighted_member):
                            notified.append(highlighted_member)
                            continue
                        # check if user can run command
                        ctx = await self.client.get_context(message)
                        if ctx is not None:
                            new_ctx = copy.copy(ctx)
                            new_ctx.author = highlighted_member
                            cmd: commands.Command = self.client.get_command('highlight')
                            if cmd is not None:
                                try:
                                    can_run = await cmd.can_run(new_ctx)
                                except:
                                    can_run = False
                                if can_run:
                                    # Check if user has channel or user ignored
                                    um = await self.client.db.fetch("SELECT ignore_type, ignore_id FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2", message.guild.id, highlighted_member.id)
                                    is_ignored = False
                                    for ignore_entry in um:
                                        if ignore_entry.get('ignore_type') == 'channel':
                                            if message.channel.id == ignore_entry.get('ignore_id'):
                                                is_ignored = True
                                                break
                                        elif ignore_entry.get('ignore_type') == 'member':
                                            if message.author.id == ignore_entry.get('ignore_id'):
                                                is_ignored = True
                                                break
                                    if not is_ignored:
                                        e = await self.generate_context(message, k)
                                        if highlighted_member is not None and (message.channel.permissions_for(highlighted_member).view_channel or highlighted_member.id == 650647680837484556):
                                            try:
                                                await highlighted_member.send(f"**{message.author.name}** mentioned \"{k}\" in **{message.guild.name}**'s **{message.channel.name}**.", embed=e, view=SingleURLButton(link=message.jump_url, text="Jump to Message", emoji="✉️`"))
                                            except:
                                                pass
                                            else:
                                                self.last_seen[v] = round(time.time()) + 90
                                        notified.append(highlighted_member.id)
