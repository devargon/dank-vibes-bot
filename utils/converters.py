import discord
from thefuzz import process

from .time import parse_timedelta
from datetime import timedelta
from discord.ext import commands
from utils.errors import ArgumentBaseError, DefaultRoleError, IntegratedRoleError, InvalidDatabase, RoleNotFound, UserNotFound
from utils.format import stringnum_toint, stringtime_duration


class BetterMessageID(commands.Converter):
    async def convert(self, ctx, argument):
        if argument is None:
            raise ArgumentBaseError(message="1You need to provide a message link or ID.")
        try:
            return int(argument)
        except ValueError:
            if not (argument.startswith('https') and 'discord.com/channels/' in argument):
                raise ArgumentBaseError(
                    message="2You did not provide a valid message link or ID. A message link should start with `https://discord.com/channels/`, `https://ptb.discord.com/channels/` or `https://canary.discord.com/channels/`.")
            split = argument.split('/')
            if split[4] == '@me':
                raise ArgumentBaseError(message="3You provided a message from DMs, I need a message from a channel.")
            else:
                try:
                    channel_id = int(split[5])
                except:
                    raise ArgumentBaseError(
                        message="4You did not provide a message link with a valid channel, or ID. A message link should start with `https://discord.com/channels/`, `https://ptb.discord.com/channels/` or `https://canary.discord.com/channels/`.")
                channel = ctx.guild.get_channel(channel_id)
                if channel is None:
                    raise ArgumentBaseError(
                        message="4You did not provide a valid message link with a valid channel, or ID.")
                else:
                    try:
                        message_id = int(split[-1])
                        if channel.get_partial_message(message_id) is not None:
                            return message_id
                    except:
                        raise ArgumentBaseError(message="5You did not provide a valid message link or ID.")

class TimedeltaConverter(commands.Converter):
    def __init__(self, *, minimum=None, maximum=None, allowed_units=None, default_units=None):
        self.allowed_units = allowed_units
        self.default_units = default_units
        self.minimum = minimum
        self.maximum = maximum

    async def convert(self, ctx, argument : str) -> timedelta:
        if self.default_units and argument.isdecimal():
                argument = argument + self.default_units

        delta = parse_timedelta(argument, minimum=self.minimum, maximum=self.maximum, allowed_units=self.allowed_units)
        if delta is not None:
            return delta
        raise ArgumentBaseError(message='Invalid time, try "30m" or "1h"')

class TrueFalse(commands.Converter):
    """
    A basic true false converter.
    'yes', 'y', 'yeah', 'true' for True
    and 'no', 'n', 'nah', 'false' for False.
    """
    async def convert(self, ctx, argument):
        if argument.lower() in ('yes', 'y', 'yeah', 'true'):
            return True
        elif argument.lower() in ('no', 'n', 'nah', 'false'):
            return False
        return False

def AllowDeny(arg: str):
    if arg.lower() in ("allow", "whitelist", "wl"):
        return True
    if arg.lower() in ("deny", "blacklist", "bl"):
        return False
    raise ArgumentBaseError(message=f'"{arg}" is not a valid option. Try "allow", "deny", "whitelist", or "blacklist"')

class ValidDatabase(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.lower() == 'database':
            return 'databases/database.db'
        elif argument.lower() == 'votetracker':
            return 'databases/votetracker.db'
        elif argument.lower() == 'autoreactor':
            return 'databases/autoreactor.db'
        elif argument.lower() == 'owo':
            return 'databases/owo.db'
        raise InvalidDatabase(argument)

class MemberUserConverter(commands.Converter):
    """
    A converter that checks if a given argument is a member or not, if it's not a member
    it'll check if it's a user or not, if not it'll raise an error.
    """
    async def convert(self, ctx, argument):
        try:
            user = await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:
            try:
                user = await commands.UserConverter().convert(ctx, argument)
            except commands.UserNotFound:
                raise UserNotFound(argument)
        return user

class BetterRoles(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            role = await commands.RoleConverter().convert(ctx, argument)
        except commands.BadArgument:
            role = discord.utils.find(lambda x: x.name.lower() == argument.lower(), ctx.guild.roles)
            if role is None:
                raise RoleNotFound(argument)
        if role.is_bot_managed():
            raise IntegratedRoleError(role.name)
        if role.is_default():
            raise DefaultRoleError(role.name)
        return role

class RoleString(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.split()
        roles = []
        for arg in args:
            try:
                role = await commands.RoleConverter().convert(ctx, argument=arg)
            except commands.BadArgument:
                role = discord.utils.find(lambda x: x.name.lower() == argument.lower(), ctx.guild.roles)
                if role is None:
                    raise RoleNotFound(argument)
            if role.is_bot_managed():
                raise IntegratedRoleError(role.name)
            if role.is_default():
                raise DefaultRoleError(role.name)
            roles.append(role)
        return roles


class BetterInt(commands.Converter):
    async def convert(self, ctx, argument:str):
        try:
            number: int = stringnum_toint(argument)
        except Exception as e:
            raise e
        if number is None:
            raise ArgumentBaseError(message=f"`{argument}` is not a valid number. Accepted formats are `123`, `1m`, `1k`, `3e6`.")
        return number

class BetterTimeConverter(commands.Converter):
    async def convert(self, ctx, argument:str):
        try:
            time: int = stringtime_duration(argument)
        except Exception as e:
            raise e
        if time is None:
            raise ArgumentBaseError(message="You have inputted an invalid time.")
        return time

class BetterBetterRoles(commands.Converter):
    async def convert(self, ctx, argument) -> discord.Role:
        try:
            return await commands.RoleConverter().convert(ctx, argument)
        except commands.BadArgument:
            role_to_return = discord.utils.find(lambda x: x.name.lower() == argument.lower(), ctx.guild.roles)
            if role_to_return is not None:
                return role_to_return
            roles_and_aliases = {}
            for r in ctx.guild.roles:
                roles_and_aliases[r.name] = r.id
                # This might be a bad idea, don't care
            try:
                name, ratio = process.extractOne(argument, [x for x in roles_and_aliases])
            except TypeError:
                raise RoleNotFound(argument)
            if ratio >= 75:
                role_to_return = discord.utils.get(ctx.guild.roles, id=roles_and_aliases[name])
                if role_to_return is None:
                    raise RoleNotFound(argument)
                return role_to_return

class BetterColor(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            arg = await commands.ColourConverter().convert(ctx, argument)
        except commands.BadArgument:
            if len(argument) == 6:
                argument = f"#{argument}"
                arg = await commands.ColourConverter().convert(ctx, argument)
            else:
                arg = None
        if not isinstance(arg, discord.Colour):
            raise ArgumentBaseError(message=f"{argument} is not a valid color.\nPlease provide a valid color in the format of:\n`#FFFFFF`\n`FFFFFF`\n`0xFFFFFF`\n`0x#FFFFFF`\n`rgb(255, 255, 255)`\nA colour name")
        else:
            return arg
