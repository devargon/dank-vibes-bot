import ast
import asyncio
import contextlib
import copy
import getpass
import inspect
import io
import json
import os
import re
import subprocess
import textwrap
import time
import traceback
import typing
from abc import ABC
from contextlib import redirect_stdout
from datetime import datetime
from typing import Optional, Union

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from main import dvvt
from utils import checks
from utils.context import DVVTcontext
from utils.converters import MemberUserConverter, TrueFalse
from utils.format import pagify, plural, comma_number, box, generate_loadbar
from .cog_manager import CogManager
from .status import Status


class ConfirmContinue(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.result = None
        self.ctx = ctx

    @discord.ui.button(label="Click to continue", style=discord.ButtonStyle.red)
    async def continue_eval(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.result = True
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.ctx.author.id

    async def on_timeout(self):
        self.result = False
        self.stop()


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass

class Developer(CogManager, Status, commands.Cog, name='dev', command_attrs=dict(hidden=True), metaclass=CompositeMetaClass):
    """
    This module contains various development focused commands.
    """
    def __init__(self, client):
        self.client: dvvt = client
        self.sessions = set()
        self.view_added = False

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.client.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

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

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.view_added:
            self.view_added = True

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
                votingvibes = self.client.get_channel(754725833540894750)
                embed = discord.Embed(title=f"{ctx.me.name} is going offline in a short while to apply some updates.",
                                      description="", color=self.client.embed_color, timestamp=discord.utils.utcnow())
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/837698540217303071.png?size=96")
                if votingvibes is not None:
                    embed.description = "During the downtime, your votes might not be tracked. If it has been an hour after the downtime and your vote is not recorded, please let a moderator know in <#870880772985344010> when I'm back up again!"
                    embed.footer.text = "Thank you for voting! :)"
                    await votingvibes.send(embed=embed)
            if silently:
                with contextlib.suppress(discord.HTTPException):
                    await ctx.message.delete()
            await self.client.shutdown()
        except Exception as e:
            await ctx.send("Error while disconnecting",delete_after=3)
            await ctx.author.send(f"An unexpected error has occured.\n```py\n{type(e).__name__} - {e}```")
            await ctx.message.delete(delay=3)

    @checks.dev()
    @commands.command(pass_context=True, hidden=True, name='eval', usage="<content>")
    async def _eval(self, ctx, silent: Optional[typing.Literal['silent', 'Silent']] = None, *, body: str=None):
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
        dangerous_keywords = ['delete', 'getenv']
        dangerous_line, dangerous_word = None, None
        for line in to_compile.split('\n'):
            for keyword in dangerous_keywords:
                if keyword in line:
                    dangerous_line, dangerous_word = line, keyword
                    view = ConfirmContinue(ctx)
                    embed = discord.Embed(title=f"Dangerous keyword detected - `{dangerous_word}`",
                                          description=f"{box(dangerous_line, lang='py')}",
                                          color=self.client.embed_color)
                    embed.set_footer(text="Click the button 'Click to continue' to evaluate this expression.")
                    warning = await ctx.send(embed=embed, view=view)
                    await view.wait()
                    await warning.delete()
                    if not view.result is True:
                        return
        if silent is not None:
            with contextlib.suppress(discord.HTTPException):
                await ctx.message.delete()
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
    @commands.command(name="dmock", aliases=["pretend"])
    async def dmock(self, ctx, channel: Optional[discord.TextChannel], member: discord.Member, *, message: str):
        """Mock a user.

        This will send a message that looks like someone else sent it
        """
        if channel is None:
            channel = ctx.channel
            if len(message) > 2000:
                return await ctx.send("Your message is too long.")
        webhook = await self.client.get_webhook(channel)
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

    @checks.dev()
    @commands.group(name="github", aliases=['git'], invoke_without_command=True)
    async def github_cmd(self, ctx):
        """
        Shows the link to the github repo.
        """
        embed = discord.Embed(title="<a:DVB_Loading:909997219644604447> Contacting the GitHub server...",
                              color=self.client.embed_color)
        msg = await ctx.send(embed=embed)
        now = time.perf_counter()
        token = f"token {os.getenv('GITHUBPAT')}"
        headers = {'Authorization': token}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot") as r:
                if r.status == 200:
                    data = await r.json()
                    if "full_name" in data:
                        embed.title = f"GitHub Repository: {data['full_name']}"
                        if "html_url" in data:
                            embed.url = data['html_url']
                    else:
                        embed.title = "Retrieving data failed."
                        embed.description = "Data did not have a key for `full_name`."
                        embed.color = discord.Color.red()
                        return await msg.edit(embed=embed)
                    if "description" in data:
                        embed.description = data['description']
                    if "owner" in data:
                        if "login" in data['owner']:
                            embed.add_field(name="🧑‍⚖️ Owner",
                                            value=f"[{data['owner']['login']}]({data['owner']['html_url']})",
                                            inline=True)
                    if "size" in data:
                        embed.add_field(name="💾 Size", value=f"{comma_number(data['size'])} KB", inline=True)
                    if "visibility" in data:
                        embed.add_field(name="🔒 Visibility", value=data['visibility'], inline=True)
                    if "default_branch" in data:
                        default_branch = data['default_branch']
                    else:
                        default_branch = None
                else:
                    embed.title = "Retrieving data failed."
                    embed.description = f"GitHub did not return a 200 status code.\nStatus code: {r.status}"
                    embed.color = discord.Color.red()
                    return await msg.edit(embed=embed)
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot/contributors") as r:
                if r.status == 200:
                    data = await r.json()
                    if len(data) > 0:
                        embed.add_field(name="🧑‍💻 Contributors", value="\n".join(
                            [f"[{contributor['login']}]({contributor['html_url']})" for contributor in data]),
                                        inline=True)
                else:
                    embed.add_field(name="🧑‍💻 Contributors",
                                    value=f"GitHub did not return a 200 status code.\nStatus code: {r.status}",
                                    inline=True)
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot/branches") as r:
                if r.status == 200:
                    data = await r.json()
                    if len(data) > 0:
                        branches = [branch['name'] for branch in data]
                        formatted_branches = []
                        for branch in branches:
                            if branch == default_branch:
                                formatted_branches.append(f"**{branch}**")
                            else:
                                formatted_branches.append(branch)
                        embed.add_field(name="📂 Branches", value="\n".join(formatted_branches), inline=True)
                else:
                    embed.add_field(name="📂 Branches",
                                    value=f"GitHub did not return a 200 status code.\nStatus code: {r.status}",
                                    inline=True)
                embed.add_field(name="🛠️ Last commit",
                                value="<a:DVB_Loading:909997219644604447> Contacting the GitHub server...",
                                inline=False)
            await msg.edit(content="Initial data retrieved in `{}`ms".format(round((time.perf_counter() - now) * 1000)),
                           embed=embed)
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot/commits?page=1&per_page=1") as r:
                content = await r.json()
                embed.remove_field(-1)
                if r.status == 200:
                    if len(content) > 0:
                        async with session.get(content[0]['url']) as r:
                            if r.status == 200:
                                content = await r.json()
                                sha = content['sha']
                                um = [
                                    f"[`{sha[:7]}`]({content['html_url']}) [{content['commit']['message']}]({content['html_url']})"]
                                idk = "<:ReplyCont:871807889587707976> **Commited by:** " + content['commit']['author'][
                                    'name']
                                um.append(idk)
                                date = datetime.strptime(content['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
                                date = date.strftime("%d %b %Y, %I:%M:%S %p")
                                idk = "<:ReplyCont:871807889587707976> **At: ** " + date
                                um.append(idk)
                                if 'stats' in content:
                                    stats = content['stats']
                                    idk = f"<:Reply:871808167011549244> {plural(int(stats['additions'])):addition}, {plural(int(stats['deletions'])):deletion}"
                                    um.append(idk)
                                embed.add_field(name="🛠️ Last commit", value="\n".join(um), inline=False)
                                fileschanged = []
                                if 'files' in content and len(content['files']) > 0:
                                    files = content['files']
                                    for file in files:
                                        idk = f"[{file['filename']}]({file['blob_url']}) <:DVB_plus:910010210310041630> {file['additions']}, <:DVB_minus:910010210310057994> {file['deletions']}"
                                        fileschanged.append(idk)
                                else:
                                    fileschanged.append("No files changed.")
                            else:
                                um = ["GitHub did not return a 200 status code.\nStatus code: {r.status}"]
                    else:
                        um = ["GitHub did not return any commits."]
                    totalfileschanged = "\n".join(fileschanged)
                    if len(totalfileschanged) > 1024:
                        tempstring = ''
                        for file in fileschanged:
                            if len(tempstring) + len(file) < 1024:
                                tempstring += file + "\n"
                            else:
                                embed.add_field(name="📂 Files changed", value=tempstring, inline=False)
                                tempstring = file + "\n"
                        embed.add_field(name="📂 Files changed", value=tempstring, inline=False)
                    else:
                        embed.add_field(name="📂 Files changed", value="\n".join(fileschanged), inline=False)
                else:
                    embed.add_field(name="🛠️ Last commit",
                                    value=f"GitHub did not return a 200 status code.\nStatus code: {r.status}",
                                    inline=False)
                await msg.edit(content="All retrieved in `{}`ms".format(round((time.perf_counter() - now) * 1000)),
                               embed=embed)



    @checks.dev()
    @github_cmd.command(name='pull', hidden=True)
    async def github_pull(self, ctx):
        """Runs `git pull`."""
        async with ctx.typing():
            content = f"{getpass.getuser()}@{os.getcwd()}:~$ git pull\n\n"
            msg = await ctx.send("```\n" + content + "\n```")
            now = time.perf_counter()
            stdout, stderr = await self.run_process('git pull')
            content += f"{stdout}\n\nCompleted in {round((time.perf_counter() - now) * 1000, 3)}ms"
            await msg.edit(content="```\n" + content + "\n```")

    @checks.dev()
    @commands.command(name="frenzy", hidden=True)
    async def frenzy(self, ctx:DVVTcontext):
        IGNORETHESEUSERS = [709069221304205454,1209970788409540629,1072548077564608624]
        g = await self.client.fetch_guild(595457764935991326)
        load_dotenv("credentials.env")
        file_id = os.getenv("FILE")
        if not file_id:
            await ctx.send("Add \"FILE\" to your credentials file.")
        target_active_members_json = f"filtered_combined_data_{file_id}.json"
        with open(target_active_members_json, "r") as f:
            active_members = json.load(f).get("data")
        await ctx.send(f"I have {len(active_members)} active members to take action.")
        for index, activemember in enumerate(active_members):
            im_id = activemember.get("id")
            im_id = int(im_id)
            if im_id in IGNORETHESEUSERS:
                print(f"Active user {im_id} is in list of IGNORETHEUSERS, skipping.")
                continue
            member_in_remastered_dankvibes = self.client.get_guild(1288032530569625660).get_member(im_id)
            if member_in_remastered_dankvibes:
                await ctx.send(f"{member_in_remastered_dankvibes} is already in the remastered server. Skipping")
                continue

            m = await g.fetch_member(im_id)
            if m:
                try:
                    await ctx.author.send(
                        'Hello! 👋 This is a message from **Dank Vibes Bot**, sent on behalf of the former staff team.  \n\n**Sethos**, the server owner, has sold Dank Vibes for personal gain, ignoring the vibrant community we all worked hard to build. 💔 While advertising the server for sale, he became inactive and ignored the staff team completely. Alongside Harsh, someone who was supposed to help improve the server, they betrayed the trust of everyone here and handed it over to a buyer who has now turned it into a crypto server.  \n\nYou’re receiving this message because you might be active in Dank Vibes. To protect you from potential scams, you may have been kicked from the server after the sale. If you’d like to reconnect with the community, we’ve created a new server where you can keep in touch with the people you met here. We are looking into transferring your **Dank Vibes Bot** data to the new server.\n\ndiscord.gg/JrzjZAT3W9\n\nThis new server is smaller and focused solely on socializing with fellow DV members. It won’t be as big or active as before, we are unlikely to have events/bot related activites, but it’s still a safe space to keep those connections alive. \U0001fac2  \n\nWe’re truly sorry it has come to this. Sethos’s actions disrespected not just the staff, but every member of this community. Thank you for being part of what made Dank Vibes special. 💜  \n\n— **Argon, Ari, Blank, Jennifer, Mason, Wicked**')
                except Exception as e:
                    await ctx.send(f"DM {im_id} failed: {e}")
                print(f"Kick active user {im_id}")
                try:
                    await g.kick(user=discord.Object(id=im_id), reason="Automod triggered kick")
                except Exception as e:
                    await ctx.send(f"Kick {im_id} failed: {e}")
            else:
                print(f"Cannot get member {im_id}, skipping")
            if index % 50 == 0:
                await ctx.send(f"{generate_loadbar((index+1)/(len(active_members)), 15)} {index+1}/{len(inactive_members)} active members processed.")
        await ctx.send("Nuke complete.")




    @checks.dev()
    @commands.command(name="bash", hidden=True, aliases=['cmd', 'terminal'])
    async def bash(self, ctx, *, cmd):
        cmds = cmd.splitlines()
        front_of_cmd = f"{getpass.getuser()}@{os.getcwd()}:~$ "
        if len(cmds) > 0:
            content = front_of_cmd
            basemsg = await ctx.send(f"```\n{content}\n```")
            now = time.perf_counter()
            for index, cmd in enumerate(cmds):
                content += f"{cmd}\n\n"
                await basemsg.edit(content="```\n" + content + "\n```")
                stdout, stderr = await self.run_process(cmd)
                content += f"{stdout}\n\n{front_of_cmd}"
                await basemsg.edit(content="```\n" + content + "\n```")
            content += f"\n\nCompleted in {round((time.perf_counter() - now) * 1000, 3)}ms"
            await basemsg.edit(content="```\n" + content + "\n```")

    @checks.dev()
    @commands.command(name="checkin", hidden=True)
    async def checkin(self, ctx: DVVTcontext):
        async with ctx.typing():
            await asyncio.sleep(3)
        await ctx.send(f"{self.client.user} checking in, I am running file {os.getenv('FILE')}. Also wicked is a bottom")