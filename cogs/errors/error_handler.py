import contextlib

import discord
from datetime import datetime
from utils.time import humanize_timedelta
from discord.ext import commands
from utils.format import print_exception
from utils.errors import ArgumentBaseError
import requests
import json
import asyncio

class ErrorHandler(commands.Cog):
    """
    A cog that handles all errors.
    """
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        The event triggered when an error is raised while invoking a command.
        """
        async def send_error(*args, **kwargs):
            await ctx.send(*args, allowed_mentions=discord.AllowedMentions(roles=False, users=False), **kwargs)
        if (cog := ctx.cog):
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return
        ignore = (commands.CommandNotFound)
        if isinstance(error, ignore):
            return
        if isinstance(error, commands.NoPrivateMessage):
            await send_error("Sowwi, you can't use this command in DMs :(", delete_after=10)
        elif isinstance(error, commands.CheckFailure):
            await send_error("Oops!, looks like you don't have enough permission to use this command.", delete_after=5)
        elif isinstance(error, commands.CommandOnCooldown):
            enabled = await ctx.bot.pool_pg.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", ctx.author.id)
            if enabled == True:
                return await ctx.reinvoke()
            message = f"You're on cooldown. Try again in **{humanize_timedelta(seconds=error.retry_after)}**."
            if ctx.command.name == "dumbfight":
                message += "\nPeople with **Vibing Investor** will have a cooldown of only **30 minutes**!"
            if ctx.command.name == "lockgen":
                message = f"This command is currently under a global cooldown of **{humanize_timedelta(seconds=error.retry_after)}** to prevent abuse.\n"
            await send_error(message)
        elif isinstance(error, commands.MemberNotFound):
            ctx.command.reset_cooldown(ctx)
            await send_error("I couldn't find a member called {}.".format(error.argument))
        elif isinstance(error, commands.RoleNotFound):
            ctx.command.reset_cooldown(ctx)
            await send_error("I couldn't find a role called {}.".format(error.argument))
        elif isinstance(error, commands.BadUnionArgument):
            ctx.command.reset_cooldown(ctx)
            if error.converters == (discord.TextChannel, discord.VoiceChannel):
                await send_error("I couldn't find that channel.")
        elif isinstance(error, commands.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
            await send_error("{} is a required argument.".format(error.param))
        elif isinstance(error, ArgumentBaseError):
            ctx.command.reset_cooldown(ctx)
            await send_error(error)
        elif isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            await send_error(error, delete_after=10)
        elif isinstance(error, discord.errors.DiscordServerError):
            sent = False
            times = 0
            while sent == False and times <= 5:
                try:
                    await asyncio.sleep(5.0)
                    await ctx.send(
                        "⚠️ While processing your command, I was unable to connect to Discord. This is an issue with Discord's servers. Try to run the command again.")
                    sent = True
                except:
                    times += 1
            await self.client.get_channel(871737028105109574).send(
                f"I encountered a Discord Server Error at {ctx.channel.mention}: {ctx.message.jump_url}")
        else:
            embed = discord.Embed(title="⚠️ Oh no!", description="Something terribly went wrong when this command was used.\n\nThe developers have been notified and it will fixed soon.", color=discord.Color.red())
            if ctx.author.id in [650647680837484556, 321892489470410763]:
                embed.add_field(name="Error", value=f"```prolog\n{error}\n```\n<#871737028105109574>")
                await send_error(embed=embed)
            else:
                embed.set_footer(text="In the meantime, do not keep running this command.")
                await send_error(embed=embed, delete_after=10)
            traceback_error = print_exception(f'Ignoring exception in command {ctx.command}:', error)
            error_message = f"**Command:** `{ctx.message.content}`\n" \
                            f"**Message ID:** `{ctx.message.id}`\n" \
                            f"**Author:** `{ctx.author}` ({ctx.author.id})\n" \
                            f"**Guild:** `{ctx.guild}` ({ctx.guild.id})\n" \
                            f"**Channel:** `{ctx.channel}` ({ctx.channel.id})\n" \
                            f"**Jump:** [`jump`]({ctx.message.jump_url})```py\n" \
                            f"{traceback_error}\n" \
                            f"```"
            await self.client.error_channel.send(content=f"<@&871740422932824095> Check this out",embed=discord.Embed(color=0xffcccb, description=error_message, timestamp=discord.utils.utcnow()).set_footer(text=f"From: {ctx.guild.name}", icon_url=ctx.guild.icon.url), allowed_mentions=discord.AllowedMentions(roles=True))