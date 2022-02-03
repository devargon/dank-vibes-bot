import asyncio
import re
import time

import discord
import datetime
from discord.ext import commands
from stemming.porter2 import stem
import copy
from utils.buttons import confirm
from utils import checks
from main import dvvt


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

    @checks.requires_roles()
    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['hl'])
    async def highlight(self, ctx, text: str = None):
        """
        Adds a text or phrase to your highlight list.
        When you don't talk after 5 minutes, you will be DMed if someone highlights you with said phrase.
        """
        if text is None:
            return await ctx.send("You need to specify text that you want to be highlighted for.")
        text = (await commands.clean_content().convert(ctx, text)).lower()
        text = stem(text)
        if len(text) < 2:
            return await ctx.send("The text you want to be highlighted for needs to be at least 2 characters long.")
        if len(text) > 50:
            return await ctx.send("The text that you want to be highlighted for can only be 50 characters long.")
        count = await self.client.pool_pg.fetchval("SELECT COUNT(*) FROM highlight WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        if count >= 15:
            return await ctx.send("You can only have a maximum of 15 highlights.")
        exising_hl = await self.client.pool_pg.fetchval("SELECT highlights FROM highlight WHERE user_id = $1 AND guild_id = $2 AND highlights = $3", ctx.author.id, ctx.guild.id, text)
        if exising_hl is None:
            await self.client.pool_pg.execute("INSERT INTO highlight(guild_id, user_id, highlights) VALUES ($1, $2, $3)", ctx.guild.id, ctx.author.id, text)
            await ctx.send(f"'{text}' has been added to your highlights.")
        else:
            await ctx.send(f"'{text}' is already in your highlights.")

    @checks.requires_roles()
    @commands.guild_only()
    @highlight.command(name="block", aliases=['ignore'])
    async def highlight_block(self, ctx, argument: ChannelOrMember = None):
        """
        Adds a member or channel to the highlight block list.
        If a user in this list highlights you, or you were highlighted in a ignored channel, you will not be notified of it.
        """
        if argument is None:
            return await ctx.send("The argument that you need to specify should be a channel or member.")
        hl_blocks = await self.client.pool_pg.fetchval("SELECT ignore_id FROM highlight_ignores WHERE user_id = $1 AND guild_id = $2 AND ignore_id = $3", ctx.author.id, ctx.guild.id, argument.id)
        if hl_blocks is None:
            if isinstance(argument, discord.Member):
                await self.client.pool_pg.execute("INSERT INTO highlight_ignores(guild_id, user_id, ignore_type, ignore_id) VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, 'member', argument.id)
            elif isinstance(argument, discord.TextChannel):
                await self.client.pool_pg.execute("INSERT INTO highlight_ignores(guild_id, user_id, ignore_type, ignore_id) VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, 'channel', argument.id)
            await ctx.send(f"**{argument.name}** has been added to your highlight block list.")
        else:
            await ctx.send(f"**{argument.name}** is already in your highlight block list.")

    @checks.requires_roles()
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
            await self.client.pool_pg.execute("DELETE FROM highlight WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        await ctx.send("All your highlights have been removed.")

    @checks.requires_roles()
    @commands.guild_only()
    @highlight.command(name="remove", aliases=['-'])
    async def highlight_remove(self, ctx, *, text: str):
        """
        Removes a phrase or text from your highlight list.
        """
        text = (await commands.clean_content().convert(ctx, text)).lower()
        text = stem(text)
        if text is None:
            return await ctx.send("You need to specify text that you want to have removed from your highlights.")
        await self.client.pool_pg.fetchval("SELECT highlights FROM highlight WHERE user_id = $1 AND guild_id = $2 AND highlights = $3", ctx.author.id, ctx.guild.id, text)
        if text is None:
            return await ctx.send("You aren't tracking this text at all 🤨")
        await self.client.pool_pg.execute("DELETE FROM highlight WHERE user_id=$1 AND guild_id=$2 AND highlights=$3", ctx.author.id, ctx.guild.id, text)
        self.conn.commit()
        await ctx.send(f"Removed '{text}' from your highlighted words.")

    @checks.requires_roles()
    @commands.guild_only()
    @highlight.command(name="show", aliases=['display', 'list'])
    async def highlight_show(self, ctx):
        """
        Shows all the phrases or text that you're tracking, along with any ignored members or channels.
        """
        if ctx.guild is None:
            return
        all_highlights = await self.client.pool_pg.fetch("SELECT highlights FROM highlight WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
        if len(all_highlights) == 0:
            hls = "You're not tracking any words yet. Use `highlight add <text>` to start tracking."
        else:
            hls = '\n'.join([highlight.get('highlights') for highlight in all_highlights])
        all_ignores = await self.client.pool_pg.fetch("SELECT ignore_id, ignore_type FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
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
                    member = ctx.guild.get_member(ignore.get('ignore_id'))
                    if member is None:
                        obj = f"{ignore.get('ignore_id')} (unknown member)"
                    else:
                        obj = f"**{member}** (user)"
                igsn.append(obj)
            igns = '\n'.join(igsn)
        embed = discord.Embed(title="You're currently tracking the following words: ", description=hls, color=self.client.embed_color)
        embed.add_field(name="You're currently ignoring the following channels/members: ", value=igns, inline=False)
        return await ctx.send(embed=embed)

    @checks.requires_roles()
    @commands.guild_only()
    @highlight.command(name="unblock", aliases=['unignore'], no_pm=True)
    async def highlight_unblock(self, ctx, argument: ChannelOrMember = None):
        """
        Removes a channel or member from your highlight ignore list.
        """
        if argument is None:
            return await ctx.send("You need to specify a channel or member to unblock.")
        hl_blocks = await self.client.pool_pg.fetchval("SELECT ignore_id FROM highlight_ignores WHERE user_id = $1 AND guild_id = $2 AND ignore_id = $3", ctx.author.id, ctx.guild.id, argument.id)
        if hl_blocks is not None:
            await self.client.pool_pg.execute("DELETE FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2 AND ignore_id = $3", ctx.guild.id, ctx.author.id, argument.id)
            await ctx.send(f"**{argument.name}** has been removed from your highlight block list.")
        else:
            await ctx.send(f"**{argument.name}** isn't in your highlight block list.")

    async def generate_context(self, msg, hl):
        fmt = []
        fmt.append(f"<:Reply:871808167011549244> [Jump to message]({msg.jump_url})")
        async for m in msg.channel.history(limit=5):
            time = m.created_at.strftime("%H:%M:%S")
            msg_content = m.content
            msg_content = msg_content if len(msg_content) < 200 else msg_content[:200] + "..."
            fmt.append(f"**[{time}] {m.author.name}:** {msg_content}")
        e = discord.Embed(title=f"**{hl}**", description='\n'.join(fmt[::-1]), color=self.client.embed_color, timestamp=discord.utils.utcnow())
        return e

    @commands.Cog.listener()
    async def on_message(self, message):
        self.last_seen[message.author.id] = round(time.time()) # Logs the user's last seen timing
        if message.guild is None:
            return
        if message.author.bot:
            return
        a = await self.client.pool_pg.fetch("SELECT highlights, user_id FROM highlight WHERE guild_id = $1", message.guild.id)
        a = [[hl_entry.get('highlights'), hl_entry.get('user_id')] for hl_entry in a] # gets all the highlights

        final_message = self.website_regex.sub('', message.content.lower())
        final_message = self.regex_pattern.sub('', final_message)
        final_message = [stem(x) for x in final_message.split()] # formats the mesasge for better parsing

        local_last_seen = self.last_seen.get(message.author.id, self.client.uptime.timestamp())  # See if the user had sent a message recently
        if (round(time.time()) - local_last_seen) < 300:

            for k, v in a:
                notified = []
                if stem(k.lower()) in final_message and message.author.id != v and v not in notified:
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
                                    um = await self.client.pool_pg.fetch("SELECT ignore_type, ignore_id FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2", message.guild.id, highlighted_member.id)
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
                                        if highlighted_member is not None and message.channel.permissions_for(highlighted_member).view_channel:
                                            try:
                                                await highlighted_member.send(f"In **{message.guild.name}**'s **{message.channel.name}**, you were highlighted with the phrase \"{k}\".", embed=e)
                                            except:
                                                pass
                                        notified.append(highlighted_member.id)

    @checks.requires_roles()
    @commands.guild_only()
    @highlight.command(name='import')
    async def highlight_import(self, ctx):
        """
        Imports your highlights from Carl-bot.
        """
        await ctx.send("**Step 1 of 2**\n**Send `-hl list` within the next 20 seconds. I will read your current Carl-bot highlights and ignores.**")
        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.lower() == '-hl list'
        try:
            msg = await self.client.wait_for('message', check=check, timeout=20)
        except asyncio.TimeoutError:
            return await ctx.send("**Timed out.** I could not detect you running `-hl list`, please try again.")
        def check(m):
            return m.author.id == 235148962103951360 and m.channel.id == ctx.channel.id and (m.content.startswith("You're not tracking") or len(m.embeds) > 0)
        try:
            msg = await self.client.wait_for('message', check=check, timeout=20.0)
        except asyncio.TimeoutError:
            return await ctx.send("**Timed out.** I could not detect Carl-bot's response, please try again.")
        if msg.content.startswith("You're not tracking"):
            return await ctx.send("**You do not have any phrases tracked with Carl-bot's highlights.** As such, there's nothing to import.")
        if len(msg.embeds) == 0:
            return await ctx.send("**Carl-bot's response was not in the expected format. (It is missing an embed.)** Please try again.")
        embed = msg.embeds[0]
        if isinstance(embed.title, str) and embed.title == "You're currently tracking the following words":
            if isinstance(embed.description, str):
                tracked = embed.description.split('\n')
                tracked = [x.strip() for x in tracked]
                tracked = [x for x in tracked if x != '']
            else:
                tracked = None
        else:
            return await ctx.send("You're currently not tracking any phrases with Carl-bot highlights.")
        ignored_channels, ignored_members = None, None
        if len(embed.fields) > 0:
            for field in embed.fields:
                if isinstance(field.name, str) and field.name == "Ignored Channels":
                    if isinstance(field.value, str):
                        ignored = field.value.split('\n')
                        ignored = [x.strip() for x in ignored]
                        ignored_channels = []
                        for ignore_entity in ignored:
                            try:
                                channel = await commands.TextChannelConverter().convert(ctx, ignore_entity)
                            except:
                                pass
                            else:
                                ignored_channels.append(channel)

                    else:
                        ignored_channels = None
                elif isinstance(field.name, str) and field.name == "Ignored Members":
                    if isinstance(field.value, str):
                        ignored = field.value.split('\n')
                        ignored = [x.strip() for x in ignored]
                        ignored_members = []
                        for ignore_entity in ignored:
                            try:
                                member = await commands.UserConverter().convert(ctx, ignore_entity)
                            except:
                                pass
                            else:
                                ignored_members.append(member)
                    else:
                        ignored_members = None
        if tracked is None and ignored_channels is None and ignored_members is None:
            return await ctx.send("There is nothing to import over from Carl-bot's highlight settings.")
        else:
            if tracked is None:
                return await ctx.send("**Carl-bot's highlight settings were not in the expected format. (It is missing the tracked phrases.)** Please try again.")
            embed = discord.Embed(title="These are the settings that will be imported over from Carl-bot's highlight settings.", color=self.client.embed_color)
            embed.add_field(name="Tracked Phrases", value='\n'.join(tracked))
            if ignored_channels is not None:
                embed.add_field(name="Ignored Channels", value='\n'.join([x.mention for x in ignored_channels]))
            if ignored_members is not None:
                embed.add_field(name="Ignored Members", value='\n'.join([str(x) for x in ignored_members]))
        confirmview = confirm(ctx, self.client, 20.0)
        confirmview.response = await ctx.send("**Step 2 of 2**\n**Confirm that I have read your highlight settings correctly.** Click `yes` if you've ensured they're imported correctly.", embed=embed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            return await ctx.send("**Your highlight settings will not be imported from Carl-bot.")
        else:
            exising_highlights = await self.client.pool_pg.fetch("SELECT highlights FROM highlight WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
            if len(exising_highlights) > 0:
                existing_highlights = [x.get('highlights') for x in exising_highlights]
            else:
                existing_highlights = []
            to_import = [(ctx.guild.id, ctx.author.id, phrase) for phrase in tracked if phrase not in existing_highlights]
            await self.client.pool_pg.executemany("INSERT INTO highlight(guild_id, user_id, highlights) VALUES ($1, $2, $3)", to_import)
            if ignored_channels is not None:
                existing_channel_ignores = await self.client.pool_pg.fetch("SELECT ignore_id FROM highlight_ignores WHERE user_id = $1 AND guild_id = $2 AND ignore_type = $3", ctx.author.id, ctx.guild.id, 'channel')
                existing_channel_ignores = [x.get('ignore_id') for x in existing_channel_ignores]
                to_import = [(ctx.guild.id, ctx.author.id, 'channel', channel.id) for channel in ignored_channels if channel.id not in existing_channel_ignores]
                await self.client.pool_pg.executemany("INSERT INTO highlight_ignores(guild_id, user_id, ignore_type, ignore_id) VALUES ($1, $2, $3, $4)", to_import)
            if ignored_members is not None:
                existing_member_ignores = await self.client.pool_pg.fetch("SELECT ignore_id FROM highlight_ignores WHERE user_id = $1 AND guild_id = $2 AND ignore_type = $3", ctx.author.id, ctx.guild.id, 'member')
                existing_member_ignores = [x.get('ignore_id') for x in existing_member_ignores]
                to_import = [(ctx.guild.id, ctx.author.id, 'member', member.id) for member in ignored_members if member.id not in existing_member_ignores]
                await self.client.pool_pg.executemany("INSERT INTO highlight_ignores(guild_id, user_id, ignore_type, ignore_id) VALUES ($1, $2, $3, $4)", to_import)
            await ctx.send("**Your highlight settings have been successfully imported from Carl-bot!**")








