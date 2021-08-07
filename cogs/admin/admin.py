import discord
from utils import checks
from discord.ext import commands
from utils.converters import BetterRoles


class Admin(commands.Cog, name='admin'):
    """
    Server Commands
    """
    def __init__(self, client):
        self.client = client

    @commands.guild_only()
    @commands.group(name='serverrule', invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def serverrule(self, ctx):
        """
        Base command for managing server rules."""
        return await ctx.help()

    @commands.guild_only()
    @serverrule.command(name='add', aliases=['set'], usage='<command> <role>')
    @commands.has_guild_permissions(administrator=True)
    async def serverrule_add(self, ctx, cmd: str = None, role: BetterRoles = None):
        """
        Add a rule to a command in this server.
        
        Required role: <@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send('Command is a required argument.')
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        if role is None:
            return await ctx.send("Role is a required argument.")
        roles = checks.get_roles(ctx.guild, command)
        if role.id in roles:
            return await ctx.send("Command rule already exists for that role.")
        checks.set_rule(ctx.guild, command, role)
        await ctx.send(f"Command rule added for {role.mention}.")

    @commands.guild_only()
    @serverrule.command(name='remove', usage='<command> <role>')
    @commands.has_guild_permissions(administrator=True)
    async def serverrule_remove(self, ctx, cmd: str = None, role: BetterRoles = None):
        """
        Remove a rule from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send('Command is a required argument.')
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        if role is None:
            return await ctx.send("Role is a required argument.")
        roles = checks.get_roles(ctx.guild, command)
        if role.id not in roles:
            return await ctx.send(f"That role is not whitelisted for `{command}`.")
        checks.remove_rule(ctx.guild, command, role)
        await ctx.send(f"Command rule removed for {role.mention}.")
    
    @commands.guild_only()
    @serverrule.command(name='clear', usage='<command>')
    @commands.has_guild_permissions(administrator=True)
    async def serverrule_clear(self, ctx, *, cmd: str):
        """
        Clear all rules from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send('Command is a required argument.')
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        roles = checks.get_roles(ctx.guild, command)
        if len(roles) == 0:
            return await ctx.send("I couldn't find a server rule for that command.")
        checks.clear_rule(ctx.guild, command)
        await ctx.send(f"Successfully removed all command rule for `{command}`")

    @commands.guild_only()
    @serverrule.command(name='view', usage='<command>')
    @commands.has_guild_permissions(administrator=True)
    async def serverrule_view(self, ctx, *, cmd: str):
        """
        Lists all rules from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send('Command is a required argument.')
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        roles = checks.get_roles(ctx.guild, command)
        if len(roles) == 0:
            return await ctx.send("I couldn't find a server rule for that command.")
        embed = discord.Embed(color=self.client.embed_color, title=f"Permissions for `{command}`")
        embed.add_field(name='Whitelisted Roles', value="\n".join([ctx.guild.get_role(r).mention for r in roles]))
        await ctx.send(embed=embed)