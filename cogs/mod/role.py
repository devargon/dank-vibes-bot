import discord
from discord.ext import commands

from utils import checks
from utils.converters import BetterRoles

class Role(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="role")
    async def role(self, ctx, member: discord.Member = None, *, role: BetterRoles = None):
        """
        Use this command to add or remove a role to a user.
        """
        if member is None:
            return await ctx.send("You need to specify a member to add a role.")
        if role is None:
            return await ctx.send(f"You need to specify a role to add to {member}.")
        if not role.is_assignable():
            return await ctx.send(
                f"You cannot add **{role.name}** to **{member}**; this may be as the role is an integration, the role of another bot, guild default roles (like `@everyone`, Booster role), or that the role is higher than my highest role.")
        if role >= ctx.author.top_role:
            return await ctx.send(
                f"You cannot add **{role.name}** to **{member}** as the role is higher than or the same as your own highest role.")
        if role in member.roles:
            try:
                await member.remove_roles(role, reason=f"Requested by {ctx.author} ({ctx.author.id})")
            except discord.Forbidden:
                return await ctx.send(f"I don't have permission to remove **{role.name}** from **{member}**.")
            await ctx.send(f"Removed **{role.name}** from **{member}**.")
        else:
            try:
                await member.add_roles(role, reason=f"Requested by {ctx.author} ({ctx.author.id})")
            except discord.Forbidden:
                return await ctx.send(f"I don't have permission to add **{role.name}** to **{member}**.")
            await ctx.send(f"Added **{role.name}** to **{member}**.")