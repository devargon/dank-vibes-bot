import asyncio
import re
import time

import discord
import datetime
from discord.ext import commands
from stemming.porter2 import stem
import copy
from utils.buttons import confirm


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
        self.client = client
        self.last_seen = {}
        self.regex_pattern = re.compile('([^\s\w]|_)+')
        self.website_regex = re.compile("https?://[^\s]*")
        self.blacklist = []

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['hl'])
    async def highlight(self, ctx, text: str = None):
        """
        Adds a text or phrase to your highlight list.
        When you don't talk after 5 minutes, you will be DMed if someone highlights you with said phrase.
        """
        message = copy.copy(ctx.message)
        if text is None:
            message.content = f"{ctx.prefix}{ctx.command.name} add"
        else:
            message.content = f"{ctx.prefix}{ctx.command} add {text}"
        new_ctx = await self.client.get_context(message, cls=type(ctx))
        await self.client.invoke(new_ctx)

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

    @commands.guild_only()
    @highlight.command(name="add", aliases=['+'], no_pm=True)
    async def highlight_add(self, ctx, text: str = None):
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
        exising_hl = await self.client.pool_pg.fetchval("SELECT highlights FROM highlight WHERE user_id = $1 AND guild_id = $2 AND highlights = $3", ctx.author.id, ctx.guild.id, text)
        if exising_hl is None:
            await self.client.pool_pg.execute("INSERT INTO highlight(guild_id, user_id, highlights) VALUES ($1, $2, $3)", ctx.guild.id, ctx.author.id, text)
            await ctx.send(f"'{text}' has been added to your highlights.")
        else:
            await ctx.send(f"'{text}' is already in your highlights.")

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
        self.last_seen[message.author.id] = discord.utils.utcnow()
        if message.guild is None:
            return
        if message.author.bot:
            return
        now = time.perf_counter()
        a = await self.client.pool_pg.fetch("SELECT highlights, user_id FROM highlight WHERE guild_id = $1", message.guild.id)
        a = [[hl_entry.get('highlights'), hl_entry.get('user_id')] for hl_entry in a]
        final_message = self.website_regex.sub('', message.content.lower())
        final_message = self.regex_pattern.sub('', final_message)
        final_message = [stem(x) for x in final_message.split()]
        for k, v in a:
            local_last_seen = self.last_seen.get(int(v), self.client.uptime)  # See if the user had sent a message recently
            if (discord.utils.utcnow() - local_last_seen).total_seconds() < 300:
                continue
            if stem(k.lower()) in final_message and message.author.id != int(v):
                um = await self.client.pool_pg.fetch("SELECT ignore_type, ignore_id FROM highlight_ignores WHERE guild_id = $1 AND user_id = $2", message.guild.id, v)
                print(um)
                for ignore_entry in um:
                    if ignore_entry.get('ignore_type') == 'channel':
                        if message.channel.id == ignore_entry.get('ignore_id'):
                            return
                    elif ignore_entry.get('ignore_type') == 'member':
                        if message.author.id == ignore_entry.get('ignore_id'):
                            return
                usr = message.guild.get_member(int(v))
                if usr.id in self.blacklist:
                    return
                e = await self.generate_context(message, k)
                if usr is not None and message.channel.permissions_for(usr).read_messages:
                    try:
                        await usr.send(f"In **{message.guild.name}**'s **{message.channel.name}**, you were highlighted with the phrase \"{k}\".", embed=e)
                    except:
                        pass
                    self.blacklist.append(usr.id)
                    await asyncio.sleep(20)
                    self.blacklist.remove(usr.id)

    @commands.slash_command(guild_ids=[871734809154707467])
    async def bonk(self, ctx, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send("You can't bonk yourself.")
        return await ctx.respond("Bonk!", ephemeral=True)
