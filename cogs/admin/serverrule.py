import discord

from main import dvvt
from utils import checks
from discord.ext import commands
from utils.format import get_command_name
from utils.converters import BetterRoles, AllowDeny

class ServerRule(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    async def get_command_rule(self, guild: discord.Guild, command_name: str):
        query = "SELECT role_id, whitelist FROM rules WHERE guild_id=$1 AND command=$2"
        roles = await self.client.db.fetch(query, guild.id, command_name)
        if roles is None:
            return roles
        whitelist = []
        blacklist = []
        for role in roles:
            if role.get('whitelist'):
                whitelist.append(role.get('role_id'))
            else:
                blacklist.append(role.get('role_id'))
        return whitelist, blacklist

    @commands.guild_only()
    @commands.group(name='serverrule', aliases=['sr'], invoke_without_command=True)
    @checks.is_owner_or_perms(manage_roles=True)
    async def serverrule(self, ctx):
        """
        Base command for managing server rules."""
        return await ctx.help()

    @commands.guild_only()
    @serverrule.command(name='add', usage='<allow_or_deny> <command> <role>')
    @checks.is_owner_or_perms(manage_roles=True)
    async def serverrule_add(self, ctx, allow_or_deny: AllowDeny = None, cmd: str = None, role: BetterRoles = None):
        """
        Add a rule to a command in this server.
        You can pass `allow` or `whitelist` to whitelist or `deny` or `blacklist` to blacklist the role.
        
        Required role: <@&663502776952815626>
        """
        if allow_or_deny is None:
            return await ctx.help()
        if cmd is None:
            return await ctx.send('Command is a required argument.')
        if not (command := self.client.get_command(cmd) or self.client.get_application_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        if role is None:
            return await ctx.send("Role is a required argument.")
        command = get_command_name(command)
        command_rule = await self.get_command_rule(ctx.guild, command)
        if not command_rule:
            query = "INSERT INTO rules VALUES ($1, $2, $3, $4)"
            values = (ctx.guild.id, command, role.id, allow_or_deny)
        else:
            whitelist, blacklist = command_rule
            if allow_or_deny:
                if role.id in whitelist:
                    return await ctx.send("That role is already whitelisted for that command.")
                if role.id not in blacklist:
                    query = "INSERT INTO rules VALUES ($1, $2, $3, $4)"
                    values = (ctx.guild.id, command, role.id, allow_or_deny)
                elif role.id in blacklist:
                    query = "UPDATE rules SET whitelist=$1 WHERE guild_id=$2 AND command=$3 AND role_id=$4"
                    values = (allow_or_deny, ctx.guild.id, command, role.id)
            else:
                if role.id in blacklist:
                    return await ctx.send("That role is already blacklisted for that command.")
                if role.id not in whitelist:
                    query = "INSERT INTO rules VALUES ($1, $2, $3, $4)"
                    values = (ctx.guild.id, command, role.id, allow_or_deny)
                elif role.id in whitelist:
                    query = "UPDATE rules SET whitelist=$1 WHERE guild_id=$2 AND command=$3 AND role_id=$4"
                    values = (allow_or_deny, ctx.guild.id, command, role.id)
        await self.client.db.execute(query, *values)
        await ctx.checkmark()
        await ctx.send(f"Command rule added for {role.mention}.")

    @commands.guild_only()
    @serverrule.command(name='remove', usage='<command> <role>')
    @checks.is_owner_or_perms(manage_roles=True)
    async def serverrule_remove(self, ctx, cmd: str = None, role: BetterRoles = None):
        """
        Remove a rule from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send('Command is a required argument.')
        if not (command := self.client.get_command(cmd) or self.client.get_application_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")

        if role is None:
            return await ctx.send("Role is a required argument.")
        command = get_command_name(command)
        command_rule = await self.get_command_rule(ctx.guild, command)
        if not command_rule:
            return await ctx.send(f"I don't have any server rule for that `{command}`.")
        whitelist, blacklist = command_rule
        if role.id not in whitelist and role.id not in blacklist:
            return await ctx.send(f"I don't have any server rule for {role.mention}.")
        await self.client.db.execute("DELETE FROM rules WHERE guild_id=$1 AND command=$2 AND role_id=$3", ctx.guild.id, command, role.id)
        await ctx.checkmark()
        await ctx.send(f"Command rule removed for {role.mention}.")
    
    @commands.guild_only()
    @serverrule.command(name='clear', usage='<command>')
    @checks.is_owner_or_perms(manage_roles=True)
    async def serverrule_clear(self, ctx, *, cmd: str):
        """
        Clear all rules from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send("Command is a required argument.")
        if not (command := self.client.get_command(cmd) or self.client.get_application_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        command = get_command_name(command)
        command_rule = await self.get_command_rule(ctx.guild, command)
        if not command_rule:
            return await ctx.send(f"I don't have any server rule for that `{command}`.")
        await self.client.db.execute("DELETE FROM rules WHERE guild_id=$1 AND command=$2", ctx.guild.id, command)
        await ctx.send(f"Successfully removed all command rule for `{command}`")

    @commands.guild_only()
    @serverrule.command(name='view', usage='<command>')
    @checks.is_owner_or_perms(manage_roles=True)
    async def serverrule_view(self, ctx, *, cmd: str):
        """
        Lists all rules from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send("Command is a required argument.")
        if not (command := self.client.get_command(cmd) or self.client.get_application_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        command_type = "Prefixed command" if isinstance(command,
                                                        commands.Command) else "Application command"
        roles = await self.get_command_rule(ctx.guild, get_command_name(command))
        if not roles:
            return await ctx.send("I couldn't find a server rule for that command.")
        whitelist, blacklist = roles
        embed = discord.Embed(color=self.client.embed_color, title=f"Permissions for `{command}` ({command_type})")
        if whitelist:
            embed.add_field(name='Whitelisted Roles', value="\n".join([ctx.guild.get_role(r).mention if ctx.guild.get_role(r) is not None else f'Deleted role: {r}' for r in whitelist]), inline=True)
        if blacklist:
            embed.add_field(name='Blacklisted Roles', value="\n".join([ctx.guild.get_role(r).mention if ctx.guild.get_role(r) is not None else f'Deleted role: {r}' for r in blacklist]), inline=True)
        if command.parent:
            embed.add_field(name="No Serverrules detected for this command", value=f"Since this is a subcommand, the permissions are inherited from the parent command, if any.")
        await ctx.send(embed=embed)