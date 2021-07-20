import discord
from discord.ext import commands
from utils.format import print_exception
from utils.time import humanize_timedelta
from utils.errors import ArgumentBaseError


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
        cog = ctx.cog
        if cog:
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
            await send_error(f"Please wait for another **{humanize_timedelta(second=error.retry_after)}** seconds before executing this command!")
        elif isinstance(error, commands.MemberNotFound):
            await send_error("I couldn't find a member called {}.".format(error.argument))
        elif isinstance(error, commands.RoleNotFound):
            await send_error("I couldn't find a role called {}.".format(error.argument))
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_error("{} is a required argument.".format(error.param))
        elif isinstance(error, ArgumentBaseError):
            await send_error(error)
        elif isinstance(error, commands.BadArgument):
            await send_error(error, delete_after=10)
        elif isinstance(error, commands.CommandError):
            await send_error(error, delete_after=10)
        else:
            msg = f"Oops! something went wrong\n{error}"
            await send_error(msg, delete_after=15)
            traceback_error = print_exception(f'Ignoring exception in command {ctx.command}:', error)
            error_message = f"**Command:** `{ctx.message.content}`\n" \
                            f"**Message ID:** `{ctx.message.id}`\n" \
                            f"**Author:** `{ctx.author}` ({ctx.author.id})\n" \
                            f"**Guild:** `{ctx.guild}` ({ctx.guild.id})\n" \
                            f"**Channel:** `{ctx.channel}` ({ctx.channel.id})\n" \
                            f"**Jump:** [`jump`]({ctx.message.jump_url})```py\n" \
                            f"{traceback_error}\n" \
                            f"```"
            await self.client.get_guild(736324402236358677).get_channel(847756191346327614).send(embed=discord.Embed(description=error_message))