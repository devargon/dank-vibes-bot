import functools
import io
import re
import ast
import copy
import time
import typing
from collections import Counter

from datetime import datetime, timezone

import matplotlib.pyplot as plt

import discord
from discord import Webhook
import asyncio
import inspect
import aiohttp
import textwrap
import traceback
import contextlib
from abc import ABC

from utils import checks
from .status import Status
from .botutils import BotUtils
from contextlib import redirect_stdout
from discord.ext import commands, menus
from .cog_manager import CogManager
from utils.format import pagify, TabularData, plural, text_to_file, get_command_name
from .maintenance import Maintenance
from.logging import Logging
from utils.converters import MemberUserConverter, TrueFalse
from typing import Optional, Union
from utils.menus import CustomMenu
from utils.context import DVVTcontext


class Suggestion(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=6)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=entry[1], inline=False)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class toggledevmode(discord.ui.View):
    def __init__(self, ctx: DVVTcontext, client, enabled):
        self.context = ctx
        self.response = None
        self.result = None
        self.client = client
        self.enabled = enabled
        super().__init__(timeout=5.0)
        init_enabled = self.enabled

        async def update_message():
            self.enabled = False if self.enabled else True
            await self.client.db.execute("UPDATE devmode SET enabled = $1 WHERE user_id = $2", self.enabled, ctx.author.id)
            self.children[0].style = discord.ButtonStyle.green if self.enabled else discord.ButtonStyle.red
            self.children[0].label = "Dev Mode is enabled" if self.enabled else "Dev mode is disabled"
            await self.response.edit(view=self)

        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await update_message()
        self.add_item(somebutton(emoji="🛠️", label = "Dev Mode is enabled" if init_enabled else "Dev mode is disabled", style=discord.ButtonStyle.green if init_enabled else discord.ButtonStyle.red))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        ctx = self.context
        author = ctx.author
        if interaction.user != author:
            await interaction.response.send_message("Only the author can interact with this message.", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass

class Developer(Logging, BotUtils, CogManager, Maintenance, Status, commands.Cog, name='dev', command_attrs=dict(hidden=True), metaclass=CompositeMetaClass):
    """
    This module contains various development focused commands.
    """
    def __init__(self, client):
        self.client = client
        self.sessions = set()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    def sanitize_output(self, input_: str) -> str:
        """Hides the bot's token from a string."""
        token = self.client.http.token
        return re.sub(re.escape(token), "[TOKEN]", input_, re.I)

    @staticmethod
    def async_compile(source, filename, mode):
        return compile(source, filename, mode, flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT, optimize=0)

    @staticmethod
    def get_pages(msg: str):
        """Pagify the given message for output to the user."""
        return pagify(msg, delims=["\n", " "], priority=True, shorten_by=10)

    @staticmethod
    def get_sql(msg: str):
        return pagify(msg, delims=["\n", " "], priority=True, shorten_by=10, box_lang='py')

    @checks.dev()
    @commands.command(hidden=True, usage='[silently]')
    async def shutdown(self, ctx, silently: TrueFalse = False):
        """
        Shuts down the bot.

        The bot will send a shutdown message, you can pass true to skip that.
        """
        try:
            await ctx.checkmark()
            if not silently:
                await ctx.send("Shutting down...")
            if silently:
                with contextlib.suppress(discord.HTTPException):
                    await ctx.message.delete()
            votingvibes = self.client.get_channel(754725833540894750)
            embed = discord.Embed(title=f"{ctx.me.name} is going offline in a short while to apply some updates.", description="", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/837698540217303071.png?size=96")
            if votingvibes is not None:
                embed.description = "During the downtime, your votes might not be tracked. If it has been an hour after the downtime and your vote is not recorded, please let a moderator know in <#870880772985344010> when I'm back up again!"
                embed.footer.text = "Thank you for voting! :)"
                await votingvibes.send(embed=embed)
            grindchannel = self.client.get_channel(862574856846704661)
            if grindchannel is not None:
                embed.description = "During the downtime, I can't track your grinder donations. Please send your 5,000,000 coins when I'm back online!"
                embed.footer.text = "Thank you for being a DV Grinder!"
                await grindchannel.send(embed=embed)
            await self.client.shutdown()
        except Exception as e:
            await ctx.send("Error while disconnecting",delete_after=3)
            await ctx.author.send(f"An unexpected error has occured.\n```py\n{type(e).__name__} - {e}```")
            await ctx.message.delete(delay=3)

    @checks.dev()
    @commands.command(pass_context=True, hidden=True, name='eval', usage="<content>")
    async def _eval(self, ctx, *, body: str=None):
        """
        Evaluate a code directly from your discord.

        The bot will always respond with the return value of the code.
        If the return value of the code is a coroutine, it will be awaited,
        and the result of that will be the bot's response.

        The code can be within a codeblock, inline code or neither, as long
        as they are not mixed and they are formatted correctly.
        """
        env = {
            'client': self.client,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'suppress': contextlib.suppress,
            'time': time,
            'asyncio': asyncio,
            'aiohttp': aiohttp,
        }
        env.update(globals())
        if body is None:
            return await ctx.send("I need something to evaluate.")

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        try:
            exec(to_compile, env)
        except SyntaxError as e:
            await ctx.crossmark()
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        ret = None
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except:
            await ctx.crossmark()
            to_print = "{}{}".format(stdout.getvalue(), traceback.format_exc())
        else:
            to_print = stdout.getvalue()
            await ctx.checkmark()

        if ret is not None:
            msg = "{}{}".format(to_print, ret)
        else:
            msg = to_print
        msg = self.sanitize_output(msg)
        await ctx.send_interactive(self.get_pages(msg), box_lang="py")

    @checks.dev()
    @commands.command(name='repl', hidden=True)
    async def repl(self, ctx):
        """
        Launches an interactive REPL session.

        The code can be within a codeblock, inline code or neither, as long
        as they are not mixed and they are formatted correctly.
        """
        variables = {
            'ctx': ctx,
            'client': self.client,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            'asyncio': asyncio,
            'aiohttp': aiohttp,
            'suppress': contextlib.suppress,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return
        self.sessions.add(ctx.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')
        await ctx.message.add_reaction('<a:DVB_typing:955345484648710154>')
        def check(m):
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id
        while True:
            try:
                response = await self.client.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.message.clear_reaction('<a:DVB_typing:955345484648710154>')
                await ctx.checkmark()
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.message.clear_reaction('<a:DVB_typing:955345484648710154>')
                await ctx.checkmark()
                await ctx.send('Exiting.')
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                try:
                    code = self.async_compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval
            if executor is exec:
                try:
                    code = self.async_compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue
            variables['message'] = response
            fmt = None
            stdout = io.StringIO()
            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except:
                value = stdout.getvalue()
                fmt = "{}{}".format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = "{}{}".format(value, result)
                    variables['_'] = result
                elif value:
                    fmt = "{}".format(value)
            try:
                if fmt is not None:
                    msg = self.sanitize_output(fmt)
                    await ctx.send_interactive(self.get_pages(msg), box_lang="py")
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')

    @checks.dev()
    @commands.command(name='sudo', aliases=['su'], hidden=True, usage='<user> <command>')
    async def sudo(self, ctx, member: MemberUserConverter = None, *, command: str = None):
        """
        Invoke a command as another user.
        """
        if member is None:
            return await ctx.send('Member is a required argument.')
        if command is None:
            return await ctx.send('Command is a required argument.')
        message = copy.copy(ctx.message)
        message.channel = ctx.channel
        message.author = member
        message.content = ctx.prefix + command
        new_ctx = await self.client.get_context(message, cls=type(ctx))
        await self.client.invoke(new_ctx)

    @checks.dev()
    @commands.group(name='sql', invoke_without_command=True, hidden=True)
    async def sql(self, ctx, *, query: str = None):
        """
        Evaluate a SQL query directly from your discord.
        """
        if query is None:
            return await ctx.send('Query is a required argument.')
        query = self.cleanup_code(query)      
        multistatement = query.count(';') > 1
        if query.lower().startswith('select') and not multistatement:
            strategy = self.client.db.fetch
        else:
            multistatement = True
            strategy = self.client.db.execute
        try:
            start = time.perf_counter()
            results = await strategy(query)
            time_taken = (time.perf_counter() - start) * 1000.0
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        rows = len(results)
        if multistatement or rows == 0:
            return await ctx.send(f'`{time_taken:.2f}ms: {results}`')
        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()
        msg = f'{render}\n*Returned {plural(len(results)):row} in {time_taken:.2f}ms*'
        if len(headers) > 2:
            return await ctx.send(file=text_to_file(msg, "sql.txt"))
        await ctx.send_interactive(self.get_sql(msg))

    @checks.dev()
    @sql.command(name='table', hidden=True, usage="<table>")
    async def sql_table(self, ctx, table: str = None):
        """
        Describes the table schema.
        """
        if table is None:
            return await ctx.send("Table is a required argument.")
        query = """SELECT column_name, data_type, column_default, is_nullable
                   FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE table_name = $1
                """
        try:
            results = await self.client.db.fetch(query, table)
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()
        msg = f'{render}'
        await ctx.send_interactive(self.get_sql(msg))

    @checks.admoon()
    @commands.command(name="dsay", aliases=["decho"])
    async def d_say(self, ctx, channel: Optional[discord.TextChannel], *, message = None):
        """
        Talk as the bot.
        """
        if message is None:
            return await ctx.send("give me something to say 🤡")
        if channel is None:
            channel = ctx.channel
        if len(message) > 2000:
            return await ctx.send(f"Your message is {len(message)} characters long. It can only be 2000 characters long.")
        try:
            await channel.send(message)
            status = (1, "Sent successfully")
            await ctx.checkmark()
        except Exception as e:
            await ctx.crossmark()
            status = (0, e)

    @checks.admoon()
    @commands.command(name="dreply")
    async def d_reply(self, ctx, messageID_or_messageLink:Union[int, str] = None, channel:Optional[discord.TextChannel] = None, *, message_content=None):
        """
        Replies to a specified message as the bot.
        Add --noping to disable pinging when replying.
        """
        #Getting message by message ID
        if type(messageID_or_messageLink) == int:
            if channel is None:
                channel = ctx.channel
            try:
                message = await channel.fetch_message(messageID_or_messageLink)
            except discord.NotFound:
                return await ctx.send(f"A message with that ID was not found. {'Did you forget to include a channel?' if channel==ctx.channel else ''}")
        else:
            if not (messageID_or_messageLink.startswith('http') and 'discord.com/channels/' in messageID_or_messageLink):
                return await ctx.send("You did not provide a valid message link or ID. A message link should start with `https://discord.com/channels/` or `https://canary.discord.com/channels/`.")
            split = messageID_or_messageLink.split('/')
            try:
                guild = self.client.get_guild(int(split[4]))
                channel = guild.get_channel(int(split[5]))
                message = await channel.fetch_message(int(split[6]))
            except discord.NotFound:
                return await ctx.send(f"A message with that link was not found. ")
        if message_content is None:
            return await ctx.send("give me something to say 🤡")
        if message_content.endswith('--noping'):
            ping=False
            message_content=message_content[:-8]
        else:
            ping=True
        if len(message_content) > 2000:
            return await ctx.send(f"Your message is {len(message_content)} characters long. It can only be 2000 characters long.")
        try:
            await message.reply(message_content, allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=ping))
            await ctx.checkmark()
            status = (1, "Sent successfully")
        except Exception as e:
            await ctx.crossmark()
            status = (0, e)

    @checks.admoon()
    @commands.command(name="error", aliases=["raiseerror"])
    async def raise_mock_error(self, ctx, *, message=None):
        """
        Raises a ValueError for testing purposes.
        """
        await ctx.send("Mimicking an error...")
        raise ValueError(message)

    @checks.dev()
    @commands.command(name="suggestions")
    async def active_suggestions(self, ctx, *, inquery: Union[int, discord.Member, str] = None):
        """
        Lists the active suggestions.
        the query can be a suggestion ID or `--active`
        """
        if inquery is None:
            embed = discord.Embed(title="Developer Suggestion Utilities", description="`--active` - list active suggestions.\n`--open` - list active suggestions.\n`--inactive` - list closed suggestions.\n`--closed` - list closed suggestions.\n`<num>` - show a specific suggestion.\n`<member>` - list suggestions from a member.", color=discord.Color.green())
            return await ctx.send(embed=embed)
        if type(inquery) == int:
            result = await self.client.db.fetchrow("SELECT * FROM suggestions WHERE suggestion_id = $1", inquery)
            if result is not None:
                member = self.client.get_user(result.get('user_id'))
                embed = discord.Embed(title=f"Suggestion {inquery}", description = result.get('suggestion'), color=self.client.embed_color)
                embed.add_field(name="Suggested by", value=f"{member} ({member.id})" if member else result.get('user_id'), inline=True)
                embed.add_field(name="Status", value="Closed" if result.get('finish') else "Open", inline=True)
                if result.get('finish'):
                    response = await self.client.db.fetchrow("SELECT * FROM suggestion_response WHERE suggestion_id = $1", inquery)
                    if response is not None:
                        responder = self.client.get_user(response.get('user_id'))
                        embed.add_field(name=f"Closed by {responder} with the remarks:", value=response.get('message'), inline=False)
                return await ctx.send(embed=embed)
            else:
                return await ctx.send(f"There is no such suggestion with the ID {inquery}.")
        if type(inquery) == discord.Member:
            query = f"SELECT * FROM suggestions WHERE user_id = $1", inquery.id
            title = f"{inquery}'s suggestions"
        elif type(inquery) == str:
            if ctx.message.content.endswith("--active") or ctx.message.content.endswith("--open"):
                query = "SELECT * FROM suggestions WHERE finish = False"
                title = "Active suggestions"
            elif ctx.message.content.endswith("--inactive") or ctx.message.content.endswith("--closed"):
                query = "SELECT * FROM suggestions WHERE finish = True"
                title = "Closed suggestions"
            elif ctx.message.content.endswith("--all"):
                query = "SELECT * FROM suggestions"
                title = "All suggestions"
            else:
                return await ctx.send("You did not provide a proper flag.")
        else:
            embed = discord.Embed(title="Developer Suggestion Utilities", description="`--active` - list active suggestions.\n`--open` - list active suggestions.\n`--inactive` - list closed suggestions.\n`--closed` - list closed suggestions.\n`<num>` - show a specific suggestion.\n`<member>` - list suggestions from a member.", color=discord.Color.green())
            return await ctx.send(embed=embed)
        if len(query) == 2:
            result = await self.client.db.fetch(query[0], query[1])
        else:
            result = await self.client.db.fetch(query)
        suggestions = []
        for suggestion in result:
            member = self.client.get_user(suggestion.get('user_id'))
            name = f"{suggestion.get('suggestion_id')}. {member} ({member.id})" if member is not None else f"{suggestion.get('suggestion_id')}. {suggestion.get('user_id')}"
            suggestions.append((name, suggestion.get('suggestion')))
        if len(suggestions) <= 6:
            embed = discord.Embed(title=title, color=self.client.embed_color, timestamp=discord.utils.utcnow())
            for suggestion in suggestions:
                embed.add_field(name=suggestion[0], value=suggestion[1], inline=False)
            return await ctx.send(embed=embed)
        else:
            pages = CustomMenu(source=Suggestion(suggestions, title), clear_reactions_after=True, timeout=60)
            return await pages.start(ctx)

    @checks.dev()
    @commands.command(name="mock", aliases=["pretend"])
    async def mock(self, ctx, channel: Optional[discord.TextChannel], member: discord.Member, *, message: str):
        """Mock a user.

        This will send a message that looks like someone else sent it
        """
        if channel is None:
            channel = ctx.channel
            if len(message) > 2000:
                return await ctx.send("Your message is too long.")
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=self.client.user.name)
        if webhook is None:
            try:
                webhook = await channel.create_webhook(name=self.client.user.name)
            except discord.Forbidden:
                try:
                    await channel.send("I am unable to create a webhook.")
                except (discord.HTTPException, discord.Forbidden):
                    return
                return
        msg = await webhook.send(message, username=member.display_name, avatar_url=member.display_avatar)
        await ctx.message.add_reaction("<a:DVB_NyaTrash:919606179590733944>")
        try:
            def check(payload):
                return payload.message_id == ctx.message.id and payload.user_id == ctx.author.id and str(payload.emoji) == "<a:DVB_NyaTrash:919606179590733944>"
            await self.client.wait_for("raw_reaction_add", check=check, timeout=10)
        except asyncio.TimeoutError:
            try:
                await ctx.message.clear_reaction("<a:DVB_NyaTrash:919606179590733944>")
                await ctx.message.add_reaction("<:DVB_True:887589686808309791>")
            except:
                pass
        else:
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass



    @checks.base_dev()
    @commands.command(name="devmode")
    async def devmode(self, ctx):
        result = await self.client.db.fetchrow("SELECT * FROM devmode WHERE user_id = $1", ctx.author.id)
        if result is None:
            await self.client.db.execute("INSERT INTO devmode VALUES($1, $2)", ctx.author.id, False)
            result = await self.client.db.fetchrow("SELECT * FROM devmode WHERE user_id = $1", ctx.author.id)
        is_enabled = result.get('enabled')
        view = toggledevmode(ctx, self.client, is_enabled)
        msg = await ctx.send("__**Toogle Developer mode**__", view=view)
        view.response = msg
        await view.wait()


    @checks.dev()
    @commands.command(name="commandusage")
    async def commandusage(self, ctx, argument: typing.Union[discord.User, discord.TextChannel, str] = None):
        """
        Shows the command usage.
        The argument can be a user, text channel, or command name.
        """
        async def create_line_chart(x_axis, y_axis, x_label, y_label, title):
            x_axis = list(x_axis)
            y_axis = list(y_axis)
            x_axis_dt_format = [datetime.fromtimestamp(x).replace(tzinfo=timezone.utc) for x in x_axis]
            for x in x_axis_dt_format:
                string = x.strftime("%a %d $b")
            plt.clf()
            fig, ax = plt.subplots()
            ax.plot(x_axis_dt_format, y_axis)
            fig.autofmt_xdate()
            plt.title(title)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.grid(True)
            def generate_graph():
                buf = io.BytesIO()
                fig.savefig(buf, format='png')
                buf.seek(0)
                return buf
            task = functools.partial(generate_graph)
            task = self.client.loop.run_in_executor(None, task)
            try:
                buf = await asyncio.wait_for(task, timeout=10)
            except asyncio.TimeoutError:
                return None
            else:
                return buf

        perf_now = time.perf_counter()
        def sort_dictionary(dictionary: dict, reverse: bool = False):
            lst = sorted(dictionary.items(), key=lambda x: x[1], reverse=reverse)
            new_dict = {}
            for item in lst:
                new_dict[item[0]] = item[1]
            return new_dict

        past_7_days = round(time.time()) - 604800
        past_24_hours = round(time.time()) - 86400
        past_30_days = round(time.time()) - 2592000

        if argument is None:
            result = await self.client.pool_pg.fetch("SELECT * FROM commandlog ORDER BY time")
            if len(result) < 10:
                resultembed = discord.Embed(title="Warning", description="Not enough command usage to produce a proper result.", color=discord.Color.red())
                file = None
            else:
                user_dict = Counter([x.get('user_id') for x in result])
                all_time_usage_dict = {}
                all_time_usage = 0
                seven_day_usage = 0
                twentyfour_hour_usage = 0
                thirty_day_usage = 0
                two_week_usage_data_per_hour = {}
                now = round(time.time())

                while len(two_week_usage_data_per_hour) < 14:
                    while now % 86400 != 0:
                        now -= 1
                    if now in two_week_usage_data_per_hour:
                        now -= 1
                    else:
                        two_week_usage_data_per_hour[now] = 0
                for command_record in result:
                    time_run = command_record.get('time')
                    all_time_usage += 1
                    if time_run > past_7_days:
                        seven_day_usage += 1
                    if time_run > past_24_hours:
                        twentyfour_hour_usage += 1
                    if time_run > past_30_days:
                        for key in two_week_usage_data_per_hour:
                            if time_run - key > 86400:
                                break
                            elif time_run - key < 0:
                                continue
                            else:
                                two_week_usage_data_per_hour[key] += 1
                                break
                        thirty_day_usage += 1
                    if command_record.get('command') not in all_time_usage_dict:
                        all_time_usage_dict[command_record.get('command')] = 1
                    else:
                        all_time_usage_dict[command_record.get('command')] += 1
                usage_sorted = sort_dictionary(all_time_usage_dict, reverse=True)
                details = f"Past 7 days: {seven_day_usage}\nPast 24 hours: {twentyfour_hour_usage}\nPast 30 days: {thirty_day_usage}\n**All time: {all_time_usage}**"
                top_usage = []
                for cmd in usage_sorted:
                    if len(top_usage) < 5:
                        top_usage.append(f"`{cmd}`: **{usage_sorted[cmd]}**")
                top_usage = '\n'.join(top_usage)
                u = await create_line_chart(two_week_usage_data_per_hour.keys(), two_week_usage_data_per_hour.values(), "Time", "Usage", "Command usage over time")
                user_sorted = sort_dictionary(user_dict, reverse=True)
                top_users = []
                for user in user_sorted:
                    if len(top_users) < 5:
                        user_obj = self.client.get_user(user) or user
                        top_users.append(f"{user_obj}: **{user_sorted[user]}**")
                top_users = '\n'.join(top_users)
                file = discord.File(u, filename="graph.png")
                resultembed = discord.Embed(title="Command Usage", color=self.client.embed_color)
                resultembed.add_field(name="Usage Statistics", value=details, inline=True)
                resultembed.add_field(name="Top 5 commands", value=top_usage, inline=True)
                resultembed.add_field(name="Top 5 users", value=top_users, inline=True)
                resultembed.set_image(url="attachment://graph.png")

        elif isinstance(argument, discord.User):
            result = await self.client.pool_pg.fetch("SELECT * FROM commandlog WHERE user_id = $1 ORDER BY time", argument.id)
            if len(result) < 10:
                resultembed = discord.Embed(title="Warning", description="Not enough command usage to produce a proper result.", color=discord.Color.red())
                file = None
            else:
                all_time_usage_dict = {}
                channel_data = {}
                all_time_usage = 0
                two_week_usage_data_per_hour = {}
                now = round(time.time())
                while len(two_week_usage_data_per_hour) < 15:
                    while now % 86400 != 0:
                        now -= 1
                    now -= 86400
                    if now in two_week_usage_data_per_hour:
                        now -= 1
                    else:
                        two_week_usage_data_per_hour[now] = 0
                for command_record in result:
                    if command_record.get('channel_id') not in channel_data:
                        channel_data[command_record.get('channel_id')] = 1
                    else:
                        channel_data[command_record.get('channel_id')] += 1
                    time_run = command_record.get('time')
                    all_time_usage += 1
                    # putting them into their respective keys is faster than iterating over the whole data
                    for key in two_week_usage_data_per_hour:
                        if time_run - key > 86400:
                            break
                        elif time_run - key < 0:
                            continue
                        else:
                            two_week_usage_data_per_hour[key] += 1
                            break
                    if command_record.get('command') not in all_time_usage_dict:
                        all_time_usage_dict[command_record.get('command')] = 1
                    else:
                        all_time_usage_dict[command_record.get('command')] += 1
                usage_sorted = sort_dictionary(all_time_usage_dict, reverse=True)
                channel_usage_sorted = sort_dictionary(channel_data, reverse=True)
                chan_data = []
                for chan in channel_usage_sorted:
                    if len(chan_data) < 5:
                        channel = self.client.get_channel(chan)
                        channel = channel.mention if channel else chan
                        chan_data.append(f"{channel}: **{channel_usage_sorted[chan]}**")
                top_usage = [f"**All time: {all_time_usage}**"]
                for cmd in usage_sorted:
                    if len(top_usage) < 6:
                        top_usage.append(f"`{cmd}`: **{usage_sorted[cmd]}**")
                top_usage = '\n'.join(top_usage)
                u = await create_line_chart(two_week_usage_data_per_hour.keys(), two_week_usage_data_per_hour.values(), "Time", "Usage", f"{argument}'s command usage over the last two weeks")
                file = discord.File(u, filename="graph.png")
                resultembed = discord.Embed(title=f"{argument}'s Command Usage", color=self.client.embed_color)
                resultembed.add_field(name="Usage Statistics", value=top_usage, inline=True)
                resultembed.add_field(name="Top used channels", value='\n'.join(chan_data), inline=True)
                resultembed.set_image(url="attachment://graph.png")
        elif isinstance(argument, discord.TextChannel):
            result = await self.client.pool_pg.fetch("SELECT * FROM commandlog WHERE channel_id = $1 ORDER BY time", argument.id)
            if len(result) < 10:
                resultembed = discord.Embed(title="Warning", description="Not enough command usage to produce a proper result.", color=discord.Color.red())
                file = None
            else:
                all_time_usage_dict = {}
                user_data = {}
                all_time_usage = 0
                two_week_usage_data_per_hour = {}
                now = round(time.time())
                while len(two_week_usage_data_per_hour) < 15:
                    while now % 86400 != 0:
                        now -= 1
                    if now in two_week_usage_data_per_hour:
                        now -= 1
                    else:
                        two_week_usage_data_per_hour[now] = 0
                for command_record in result:
                    if command_record.get('user_id') not in user_data:
                        user_data[command_record.get('user_id')] = 1
                    else:
                        user_data[command_record.get('user_id')] += 1
                    time_run = command_record.get('time')
                    all_time_usage += 1
                    # putting them into their respective keys is faster than iterating over the whole data
                    for key in two_week_usage_data_per_hour:
                        if time_run - key > 86400:
                            break
                        elif time_run - key < 0:
                            continue
                        else:
                            two_week_usage_data_per_hour[key] += 1
                            break
                    if command_record.get('command') not in all_time_usage_dict:
                        all_time_usage_dict[command_record.get('command')] = 1
                    else:
                        all_time_usage_dict[command_record.get('command')] += 1
                usage_sorted = sort_dictionary(all_time_usage_dict, reverse=True)
                user_data_sorted = sort_dictionary(user_data, reverse=True)
                user_data = []
                for user in user_data_sorted:
                    if len(user_data) < 5:
                        user_obj = self.client.get_user(user) or user
                        user_data.append(f"{user_obj}: **{user_data_sorted[user]}**")
                top_usage = [f"**All time: {all_time_usage}**"]
                for cmd in usage_sorted:
                    if len(top_usage) < 6:
                        top_usage.append(f"`{cmd}`: **{usage_sorted[cmd]}**")
                top_usage = '\n'.join(top_usage)
                u = await create_line_chart(two_week_usage_data_per_hour.keys(), two_week_usage_data_per_hour.values(), "Time", "Usage", f"{argument.mention}'s command usage over the last two weeks")
                file = discord.File(u, filename="graph.png")
                resultembed = discord.Embed(title=f"{argument.name}'s Command Usage", color=self.client.embed_color)
                resultembed.add_field(name="Usage Statistics", value=top_usage, inline=True)
                resultembed.add_field(name="Top used users", value='\n'.join(user_data), inline=True)
                resultembed.set_image(url="attachment://graph.png")
        elif isinstance(argument, str):
            cmd = self.client.get_command(argument)
            if cmd is None:
                resultembed = discord.Embed(title="Warning", description="Command not found. The argument passed can be a **Channel**, **Member**, **Command** or Nothing.", color=discord.Color.red())
                file = None
            else:
                full_cmd = get_command_name(cmd)
                result = await self.client.pool_pg.fetch("SELECT * FROM commandlog WHERE command = $1 ORDER BY time", full_cmd)
                if len(result) < 10:
                    resultembed = discord.Embed(title="Warning", description="Not enough command usage to produce a proper result.", color=discord.Color.red())
                    file = None
                else:
                    channel_data = Counter([x.get('channel_id') for x in result])
                    user_data = Counter([x.get('user_id') for x in result])
                    all_time_usage = 0
                    seven_day_usage = 0
                    twentyfour_hour_usage = 0
                    thirty_day_usage = 0
                    two_week_usage_data_per_hour = {}
                    now = round(time.time())

                    while len(two_week_usage_data_per_hour) < 30:
                        while now % 86400 != 0:
                            now -= 1
                        if now in two_week_usage_data_per_hour:
                            now -= 1
                        else:
                            two_week_usage_data_per_hour[now] = 0
                    for command_record in result:
                        time_run = command_record.get('time')
                        all_time_usage += 1
                        if time_run > past_7_days:
                            seven_day_usage += 1
                        if time_run > past_24_hours:
                            twentyfour_hour_usage += 1
                        if time_run > past_30_days:
                            for key in two_week_usage_data_per_hour:
                                if time_run - key > 86400:
                                    break
                                elif time_run - key < 0:
                                    continue
                                else:
                                    two_week_usage_data_per_hour[key] += 1
                                    break
                            thirty_day_usage += 1
                    channel_data_sorted = sort_dictionary(channel_data, reverse=True)
                    user_data_sorted = sort_dictionary(user_data, reverse=True)
                    channel_data = []
                    for channel in channel_data_sorted:
                        if len(channel_data) < 5:
                            channel_obj = self.client.get_channel(channel) or channel
                            channel_data.append(f"{channel_obj}: **{channel_data_sorted[channel]}**")
                    user_data = []
                    for user in user_data_sorted:
                        if len(user_data) < 5:
                            user_obj = self.client.get_user(user) or user
                            user_data.append(f"{user_obj}: **{user_data_sorted[user]}**")
                    u = await create_line_chart(two_week_usage_data_per_hour.keys(), two_week_usage_data_per_hour.values(), "Time", "Usage", f"{full_cmd}'s usage over 30 days")
                    file = discord.File(u, filename="graph.png")
                    resultembed = discord.Embed(title=f"`{full_cmd}` Usage", color=self.client.embed_color)
                    resultembed.add_field(name="Top used channels", value='\n'.join(channel_data), inline=True)
                    resultembed.add_field(name="Top used users", value='\n'.join(user_data), inline=True)
                    resultembed.set_image(url="attachment://graph.png")
        else:
            resultembed = None
            file = None
        done = round(time.perf_counter() - perf_now, 3)
        resultembed.timestamp = discord.utils.utcnow()
        resultembed.set_footer(icon_url=self.client.user.display_avatar.url, text=f"Processing completed in {done} seconds.")
        await ctx.send(f"Completed in {done}s", embed=resultembed, file=file)