import discord
from discord.ext import commands
from utils.format import proper_userf

class L2LVC(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if member.guild.id != 1288032530569625660:
            return
        l2lrole = member.guild.get_role(798074726458982420)
        if before.channel == after.channel:
            return
        if after.channel is not None:
            if after.channel.id == 838437334553985045:
                await member.add_roles(l2lrole, reason=f"{proper_userf(member)} joined the Last to Leave VC") # if member joined (from anywhere)
            elif before.channel is not None and before.channel.id == 838437334553985045:
                await member.remove_roles(l2lrole, reason=f"{proper_userf(member)} left the Last to Leave VC") # if member left L2L vc to another vc
        elif before.channel is not None and before.channel.id == 838437334553985045:
            await member.remove_roles(l2lrole, reason=f"{proper_userf(member)} left the Last to Leave VC") # if member left L2L VC
