import io
import re
import ast
import copy
import time
import sqlite3
import discord
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
from utils.format import pagify, TabularData, plural
from utils.converters import MemberUserConverter, TrueFalse, ValidDatabase

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass

class Developer(BotUtils, CogManager, Status, commands.Cog, name='dev', command_attrs=dict(hidden=True), metaclass=CompositeMetaClass):
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

    @checks.admoon()
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

    @checks.admoon()
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
        message = copy.copy(ctx.message)
        message.channel = ctx.channel
        message.author = member
        message.content = ctx.prefix + command
        new_ctx = await self.client.get_context(message, cls=type(ctx))
        await self.client.invoke(new_ctx)

    @checks.admoon()        
    @commands.group(name='sql', invoke_without_command=True, hidden=True)
    async def sql(self, ctx):
        """
        Base command for interacting with SQL.
        """
        await ctx.help()

    @checks.admoon()    
    @sql.command(name='fetch', hidden=True, usage='<database> <query...>')
    async def sql_fetch(self, ctx, db: ValidDatabase = None, *, query: str = None):
        """
        Fetches all rows of a query result.
        """
        if db is None:
            return await ctx.send('Database is a required argument.')
        if query is None:
            return await ctx.send('Query is a required argument.')
        query = self.cleanup_code(query)
        conn = sqlite3.connect(db, timeout=5)
        cur = conn.cursor()
        try:
            start = time.perf_counter()
            results = cur.execute(query)
            time_taken = (time.perf_counter() - start) * 1000.0
        except Exception:
            cur.close()
            conn.close()
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        headers = list(col_name[0] for col_name in results.description)
        table = TabularData()
        table.set_columns(headers)
        results = results.fetchall()
        cur.close()
        conn.close()
        table.add_rows(list(r) for r in results)
        render = table.render()
        msg = f'{render}\n*Returned {plural(len(results)):row} in {time_taken:.2f}ms*'
        await ctx.send_interactive(self.get_sql(msg))
    
    @checks.admoon()    
    @sql.command(name='execute', aliases=['exec'], hidden=True, usage='<database> <query...>')
    async def sql_execute(self, ctx, db: ValidDatabase = None, *, query: str = None):
        """
        Executes a SQL query.
        
        It can only execute a single SQL query.
        It also calls commit() method to commit the current changes, so be careful.
        """
        if db is None:
            return await ctx.send('Database is a required argument.')
        if query is None:
            return await ctx.send('Query is a required argument.')
        query = self.cleanup_code(query)
        conn = sqlite3.connect(db, timeout=5)
        cur = conn.cursor()
        try:
            cur.execute(query)
            await ctx.checkmark()
        except Exception:
            await ctx.crossmark()
            cur.close()
            conn.close()
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        conn.commit()
        cur.close()
        conn.close()