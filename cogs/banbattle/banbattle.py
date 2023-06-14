import random

import discord
import asyncio
import contextlib

import typing
from utils.time import humanize_timedelta
from utils.format import proper_userf
from utils import checks
from utils.buttons import *
from discord.ext import commands

DV_STAFF = 827882465452097547
SPECTATOR = 830008994658648066
PARTICIPANT = 813886794151493632
ACTIVE_SHIELD = 828838727903346688
AVAILABLE_SHIELD = 830214581989015572
BANSHIELD_LOGS = 827799467393679361

def participant_or_permissions(**perms):
    original = commands.has_permissions(**perms).predicate
    async def extended_check(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        participant = PARTICIPANT
        id = int(participant)
        role = discord.utils.get(ctx.author.roles, id=id)
        check = True if role is not None else False
        return check or await original(ctx)
    return commands.check(extended_check)

class BanBattle(commands.Cog, name='banbattle'):
    """
    Banbattle commands
    """
    def __init__(self, client):
        self.client = client
        self.scores = {}

    @staticmethod
    def pass_hierarchy_check(ctx, member: discord.Member):
        return ctx.guild.me.top_role > member.top_role

    @staticmethod
    def pass_user_hierarchy_check(ctx, member: discord.Member):
        return ctx.author.top_role > member.top_role or ctx.author == ctx.guild.owner

    def leaderboard(self, ctx):
        order = list(reversed(sorted(self.scores, key=lambda m: self.scores[m])))
        msg = []
        for i, user_id in enumerate(order[:3]):
            msg.append(f"**#{i+1}** <@{user_id}>: `{self.scores[user_id]}`")
        final_message = "__**BANBATTLE LEADERBOARD**__\n\n"
        return final_message + "\n".join(msg)

    @checks.is_dvbm()
    @commands.command(name='bon')
    @participant_or_permissions(kick_members=True)
    async def bon(self, ctx, member: discord.Member = None):
        if ctx.guild.id != 813865065593176145:
            return
        if member is None:
            return await ctx.send('You need to include a member to bon.')
        if ctx.author == member:
            return await ctx.send("You can't bon yourself.")
        if member == ctx.guild.me:
            return await ctx.send("Umm that's me-")
        if not self.pass_hierarchy_check(ctx, member):
            return await ctx.send("I cannot do that action because that role is above my highest role.")
        if discord.utils.get(member.roles, id=ACTIVE_SHIELD):
            # Checks if the member has an active shield or not.
            return await ctx.send('Member has an active shield.')
        if discord.utils.get(member.roles, id=SPECTATOR):
            # Checks if the member is a spectator or not.
            return await ctx.send("Let them spectate.")
        if not discord.utils.get(member.roles, id=PARTICIPANT):
            # Checks if the member is a participant or not.
            return await ctx.send("That member isn't a participant.")
        if not ctx.author.top_role >= member.top_role or ctx.author == ctx.guild.owner:
            return await ctx.send("You cannot do this action due to role hierarchy.")
        try:
            await ctx.guild.kick(member, reason = "Bonned by {}".format(ctx.author))
            with contextlib.suppress(KeyError):
                self.scores[ctx.author.id] += 1
            await ctx.send("Bonned **{}**".format(member))
        except Exception:
            await ctx.send("An unexpected error occurred.", delete_after=5)

    @checks.is_dvbm()
    @commands.command(name="banshield")
    async def banshield(self, ctx, member: typing.Optional[discord.Member] = None):
        if ctx.guild.id != 813865065593176145:
            return
        if member is None:
            member = ctx.author

        active_shield_role = ctx.guild.get_role(ACTIVE_SHIELD)
        available_shield_role = ctx.guild.get_role(AVAILABLE_SHIELD)
        spectator_role = ctx.guild.get_role(SPECTATOR)
        if active_shield_role in member.roles:
            return await ctx.send(f"{'You already have' if ctx.author == member else f'**{proper_userf(member)}** already has'} an active shield.")
        if available_shield_role in ctx.author.roles:
            if spectator_role in member.roles:
                if member == ctx.author:
                    return await ctx.send("You can't use your banshield on yourself as you're already eliminated.")
                else:
                    return await ctx.send(f"You can't use your banshield on **{proper_userf(member)}** as they're already eliminated.")
            else:
                duration = random.randint(5, 20)
                await ctx.send(f"Banshield activated for {humanize_timedelta(seconds=duration)}!", delete_after=3.0)
                descriptions = []
                descriptions.append(f"Activated by: `{ctx.author}` {ctx.author.mention} (`{ctx.author.id}`)")
                if ctx.author != member:
                    descriptions.append(f"Used on: `{proper_userf(member)}` {member.mention} (`{member.id}`)")
                descriptions.append(f"Duration: **{humanize_timedelta(seconds=duration)}**")
                embed = discord.Embed(title="Banshield activated!", description="\n".join(descriptions), color=self.client.embed_color)
                await ctx.guild.get_channel(BANSHIELD_LOGS).send(embed=embed)
                with contextlib.suppress(discord.HTTPException):
                    await ctx.author.remove_roles(available_shield_role)
                with contextlib.suppress(discord.HTTPException):
                    await member.add_roles(active_shield_role)
                descriptions = f"User: `{proper_userf(member)}` {member.mention}\nID: `{member.id}`\nDuration: **{humanize_timedelta(seconds=duration)}**"
                dm_embed = discord.Embed(title="Banshield Activated!", description=descriptions, color=self.client.embed_color)
                with contextlib.suppress(discord.Forbidden):
                    await ctx.author.send("Your banshield has been activated!", embed=dm_embed)
                if ctx.author != member:
                    with contextlib.suppress(discord.Forbidden):
                        await member.send(f"{ctx.author} has activated a **{humanize_timedelta(seconds=duration)}** banshield on you.", embed=dm_embed)
                await asyncio.sleep(duration)
                with contextlib.suppress(discord.HTTPException):
                    await member.remove_roles(active_shield_role)

        else:
            return await ctx.send("Looks like you've already used your shield!")


    @checks.is_dvbm()
    @commands.group(name='banbattle')
    @checks.has_permissions_or_role(manage_roles=True)
    async def banbattle(self, ctx):
        """
        Base command for Banbattle.
        """
        pass

    @checks.is_dvbm()
    @banbattle.command(name='start')
    @checks.has_permissions_or_role(manage_roles=True)
    async def banbattle_start(self, ctx):
        """
        Starts a banbattle.

        It'll add the shield role to all participants.
        You need at least 2 participants to start a banbattle.
        """
        if ctx.guild.id != 813865065593176145:
            return
        participant = ctx.guild.get_role(PARTICIPANT)
        available_shield = ctx.guild.get_role(AVAILABLE_SHIELD)
        if len(participant.members) <= 2:
            return await ctx.send('Not enough participants to start a banbattle.')
        members = [member for member in participant.members if available_shield not in member.roles]
        done = []
        if members:
            async with ctx.typing():
                for member in members:
                    with contextlib.suppress(discord.HTTPException):
                        await member.add_roles(available_shield)
                        done.append(member)
                self.scores = {p.id: 0 for p in participant.members}
            await ctx.send("Added {} role to `{}` members".format(available_shield.mention, len(done)), allowed_mentions=discord.AllowedMentions(roles=False))
            await ctx.trigger_typing()
        await asyncio.sleep(2)
        confirmView = confirm(ctx, self.client, 30.0)
        message = await ctx.send("Do you wanna unlock the channels? `Yes`|`No`", view=confirmView)
        confirmView.response = message
        await confirmView.wait()
        if confirmView.returning_value is None:
            await ctx.send('Aborting...')
            return await ctx.send('You can manually unlock the channels.')
        elif confirmView.returning_value == True:
            async with ctx.typing():
                channels = [ctx.guild.get_channel(channel) for channel in
                            [829770172285976606, 829769980709961758, 829770015187140608, 829770052378689565]]
                for channel in channels:
                    current_perms = channel.overwrites_for(ctx.guild.default_role)
                    if current_perms.send_messages != False:
                        continue
                    current_perms.update(send_messages=None)
                    with contextlib.suppress(Exception):
                        await channel.set_permissions(ctx.guild.default_role, overwrite=current_perms)
            return await ctx.send('Channels are now unlocked.')
        elif confirmView.returning_value == False:
            await ctx.send('Aborting...')
            return await ctx.send('You can manually unlock the channels.')

    @checks.is_dvbm()
    @banbattle.command(name='leaderboard', aliases=['lb'])
    @checks.has_permissions_or_role(manage_roles=True)
    async def banbattle_leaderboard(self, ctx):
        """
        Shows the leaderboard for a banbattle.
        """
        if len(self.scores) == 0:
            return await ctx.send('Start a banbattle first.')
        return await ctx.send(self.leaderboard(ctx), allowed_mentions=discord.AllowedMentions(users=False))

    @checks.is_dvbm()
    @banbattle.command(name='end', aliases=['clear'])
    @checks.has_permissions_or_role(manage_roles=True)
    async def banbattle_end(self, ctx):
        """
        Ends a banbattle.

        It'll kick all the members with `Spectator` and `Participants` role.
        """
        if ctx.guild.id != 813865065593176145:
            return
        particpants = ctx.guild.get_role(PARTICIPANT).members
        spectators = ctx.guild.get_role(SPECTATOR).members
        invites = await ctx.guild.invites()
        async with ctx.typing():
            if invites:
                for invite in invites:
                    with contextlib.suppress(Exception):
                        await invite.delete()
            channels = [ctx.guild.get_channel(channel) for channel in [829770172285976606, 829769980709961758, 829770015187140608, 829770052378689565]]
            for channel in channels:
                current_perms = channel.overwrites_for(ctx.guild.default_role)
                if current_perms.send_messages == False:
                    continue
                current_perms.update(send_messages=False)
                with contextlib.suppress(Exception):
                    await channel.set_permissions(ctx.guild.default_role, overwrite=current_perms)
            if spectators:
                for member in spectators:
                    with contextlib.suppress(Exception):
                        await ctx.guild.kick(member)
            if particpants:
                for member in particpants:
                    with contextlib.suppress(Exception):
                        await ctx.guild.kick(member)
            return await ctx.send('Successfully kicked all the participants.')