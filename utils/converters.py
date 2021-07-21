import discord
from .time import parse_timedelta
from datetime import timedelta
from discord.ext import commands
from utils.errors import ArgumentBaseError, DefaultRoleError, IntegratedRoleError, RoleNotFound, UserNotFound

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
        if role.managed or role.is_integration():
            raise IntegratedRoleError(role.name)
        if role.is_default():
            raise DefaultRoleError
        return role