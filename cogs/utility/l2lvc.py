import discord
from discord.ext import commands

class L2LVC(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if member.guild.id != 595457764935991326:
            return
        l2lrole = member.guild.get_role(798074726458982420)
        if before.channel == after.channel:
            return
        if after.channel is not None:
            if after.channel.id == 838437334553985045:
                await member.add_roles(l2lrole, reason=f"{member} joined the Last to Leave VC") # if member joined (from anywhere)
            elif before.channel is not None and before.channel.id == 838437334553985045:
                await member.remove_roles(l2lrole, reason=f"{member} left the Last to Leave VC") # if member left L2L vc to another vc
        elif before.channel is not None and before.channel.id == 838437334553985045:
            await member.remove_roles(l2lrole, reason=f"{member} left the Last to Leave VC") # if member left L2L VC
