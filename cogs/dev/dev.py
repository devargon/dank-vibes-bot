import io
import re
import ast
import copy
import time
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
from discord.ext import commands
from .cog_manager import CogManager
from utils.format import pagify, TabularData, plural, text_to_file
from .maintenance import Maintenance
from utils.converters import MemberUserConverter, TrueFalse
from typing import Optional, Union

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass

class Developer(BotUtils, CogManager, Maintenance, Status, commands.Cog, name='dev', command_attrs=dict(hidden=True), metaclass=CompositeMetaClass):
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
            await self.client.shutdown()
        except Exception as e:
            await ctx.send("Error while disconnecting",delete_after=3)
            await ctx.author.send(f"An unexpected error has occured.\n```py\n{type(e).__name__} - {e}```")
            await ctx.message.delete(delay=3)

    @checks.admoon()
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
        await ctx.message.add_reaction('<a:typing:839487089304141875>')
        def check(m):
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id
        while True:
            try:
                response = await self.client.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.message.clear_reaction('<a:typing:839487089304141875>')
                await ctx.checkmark()
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.message.clear_reaction('<a:typing:839487089304141875>')
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

    @checks.admoon()
    @commands.command(name='sudo', aliases=['su'], hidden=True, usage='<user> <command>')
    async def sudo(self, ctx, member: MemberUserConverter = None, *, command: str = None):
        """
        Invoke a command as another user.
        """
        if member is None:
            return await ctx.send('Member is a required argument.')
        if command is None:
            return await ctx.send('Command is a required argument.')
        if ctx.author.id == 515725341910892555:
            return await ctx.send('no')
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
            strategy = self.client.pool_pg.fetch
        else:
            multistatement = True
            strategy = self.client.pool_pg.execute
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
            results = await self.client.pool_pg.fetch(query, table)
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
    @commands.group(name="d", invoke_without_command=True)
    async def d_base(self, ctx):
        """
        Commands to talk as the bot.
        """
        return await ctx.help()

    @checks.admoon()
    @d_base.command(name="say", aliases=["echo"])
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
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url('https://canary.discord.com/api/webhooks/883198776406339624/mkno5cQXKLHtQH4bxbbx8kxis3qnvTbvJVxpvCM0JNLZC_kG5F8sicwSBwsxa-Gq8f90', adapter=session)
            embed=discord.Embed(title=f"Echo action executed with {ctx.me}", description=message, color=discord.Color.green() if status[0] == 1 else discord.Color.red())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Status", value=f"**{status[1]}**", inline=True)
            await webhook.send(embed=embed)

    @checks.admoon()
    @d_base.command(name="reply")
    async def d_reply(self, ctx, messageID_or_messageLink:Union[int, str] = None, channel:Optional[discord.TextChannel] = None, *, message_content=None):
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
                print(guild.name, channel.name)
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
            print(ping)
            await message.reply(
                message_content,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=ping),
            )

            await ctx.checkmark()
            status = (1, "Sent successfully")
        except Exception as e:
            await ctx.crossmark()
            status = (0, e)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url('https://canary.discord.com/api/webhooks/883198776406339624/mkno5cQXKLHtQH4bxbbx8kxis3qnvTbvJVxpvCM0JNLZC_kG5F8sicwSBwsxa-Gq8f90', adapter=session)
            embed=discord.Embed(title=f"Message replied {ctx.me}", description=message_content, color=discord.Color.green() if status[0] == 1 else discord.Color.red())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Status", value=f"**{status[1]}**", inline=True)
            embed.add_field(name="Referenced Message", value=f"Author: {message.author}\nAt: <t:{round(message.created_at.timestamp()) + 28800}>\nChannel: {message.channel}\nURL: [`Jump to message`]({message.jump_url})", inline=False)
            await webhook.send(embed=embed)
