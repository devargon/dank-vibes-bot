import asyncio
import discord
from utils import checks
from datetime import datetime
from discord.ext import commands
from utils.format import get_command_name
from utils.converters import AllowDeny, BetterRoles

class Admin(commands.Cog, name='admin'):
    """
    Server Commands
    """
    def __init__(self, client):
        self.client = client

    async def get_command_rule(self, guild: discord.Guild, command_name: str):
        query = "SELECT role_id, whitelist FROM rules WHERE guild_id=$1 AND command=$2"
        roles = await self.client.pool_pg.fetch(query, guild.id, command_name)
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
    @checks.is_owner_or_perms(administrator=True)
    async def serverrule(self, ctx):
        """
        Base command for managing server rules."""
        return await ctx.help()

    @commands.guild_only()
    @serverrule.command(name='add', usage='<allow_or_deny> <command> <role>')
    @checks.is_owner_or_perms(administrator=True)
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
        if not (command := self.client.get_command(cmd)):
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
        await self.client.pool_pg.execute(query, *values)
        await ctx.checkmark()
        await ctx.send(f"Command rule added for {role.mention}.")

    @commands.guild_only()
    @serverrule.command(name='remove', usage='<command> <role>')
    @checks.is_owner_or_perms(administrator=True)
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
        command = self.get_command_name(command)
        command_rule = await self.get_command_rule(ctx.guild, command)
        if not command_rule:
            return await ctx.send(f"I don't have any server rule for that `{command}`.")
        whitelist, blacklist = command_rule
        if role.id not in whitelist and role.id not in blacklist:
            return await ctx.send(f"I don't have any server rule for {role.mention}.")
        await self.client.pool_pg.execute("DELETE FROM rules WHERE guild_id=$1 AND command=$2 AND role_id=$3", ctx.guild.id, command, role.id)
        await ctx.checkmark()
        await ctx.send(f"Command rule removed for {role.mention}.")
    
    @commands.guild_only()
    @serverrule.command(name='clear', usage='<command>')
    @checks.is_owner_or_perms(administrator=True)
    async def serverrule_clear(self, ctx, *, cmd: str):
        """
        Clear all rules from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send("Command is a required argument.")
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        command = self.get_command_name(command)
        command_rule = await self.get_command_rule(ctx.guild, command)
        if not command_rule:
            return await ctx.send(f"I don't have any server rule for that `{command}`.")
        await self.client.pool_pg.execute("DELETE FROM rules WHERE guild_id=$1 AND command=$2", ctx.guild.id, command)
        await ctx.send(f"Successfully removed all command rule for `{command}`")

    @commands.guild_only()
    @serverrule.command(name='view', usage='<command>')
    @checks.is_owner_or_perms(administrator=True)
    async def serverrule_view(self, ctx, *, cmd: str):
        """
        Lists all rules from a command in this server.
        
        Required role:<@&663502776952815626>
        """
        if cmd is None:
            return await ctx.send("Command is a required argument.")
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        roles = await self.get_command_rule(ctx.guild, self.get_command_name(command))
        if not roles:
            return await ctx.send("I couldn't find a server rule for that command.")
        whitelist, blacklist = roles
        embed = discord.Embed(color=self.client.embed_color, title=f"Permissions for `{command}`")
        if whitelist:
            embed.add_field(name='Whitelisted Roles', value="\n".join([ctx.guild.get_role(r).mention for r in whitelist]), inline=True)
        if blacklist:
            embed.add_field(name='Blacklisted Roles', value="\n".join([ctx.guild.get_role(r).mention for r in blacklist]), inline=True)
        await ctx.send(embed=embed)

    async def handle_toggle(self, guild, settings) -> bool:
        if (result := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", guild.id, settings)) is not None:
            result = result.get('enabled')
        else:
            await self.client.pool_pg.execute("INSERT INTO serverconfig VALUES ($1, $2, $3)", guild.id, settings, False)
            result = False
        if result:
            result = False
        else:
            result = True
        await self.client.pool_pg.execute("UPDATE serverconfig SET enabled=$1 WHERE guild_id=$2 AND settings=$3", result, guild.id, settings)
        return result

    @commands.command(name='leaderboards')
    @commands.has_guild_permissions(administrator=True)
    async def leaderboards(self, ctx):
        """
        Shows guild's leaderboard settings and also allows you to allow/disable them.
        """
        def get_emoji(enabled):
            if enabled:
                return "<:DVB_enabled:872003679895560193>"
            return "<:DVB_disabled:872003709096321024>"
        embed = discord.Embed(title=f"Leaderboard Settings For {ctx.guild.name}", color=self.client.embed_color, timestamp=datetime.utcnow())
        if (owodaily := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "owodailylb")) is not None:
            owodaily = owodaily.get('enabled')
        if (owoweekly := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "owoweeklylb")) is not None:
            owoweekly = owoweekly.get('enabled')
        if (votelb := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "votelb")) is not None:
            votelb = votelb.get('enabled')
        embed.add_field(name=f"{get_emoji(owodaily)} OwO Daily Leaderboard", value=f"{'Enabled' if owodaily else 'Disabled'}", inline=False)
        embed.add_field(name=f"{get_emoji(owoweekly)} OwO Weekly Leaderboard", value=f"{'Enabled' if owoweekly else 'Disabled'}", inline=False)
        embed.add_field(name=f"{get_emoji(votelb)} Vote Leaderboard", value=f"{'Enabled' if votelb else 'Disabled'}", inline=False)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        message = await ctx.send(embed=embed)
        emojis = ['1⃣', '2⃣', '3⃣', 'ℹ']
        for emoji in emojis:
            await message.add_reaction(emoji)
        def check(payload):
                return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(payload.emoji) in emojis
        while True:
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
            except asyncio.TimeoutError:
                return await message.clear_reactions()
            if str(response.emoji) == emojis[0]:
                owodaily = await self.handle_toggle(ctx.guild, "owodailylb")
                embed.set_field_at(index=0, name=f"{get_emoji(owodaily)} OwO Daily Leaderboard", value=f"{'Enabled' if owodaily else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[1]:
                owoweekly = await self.handle_toggle(ctx.guild, 'owoweeklylb')
                embed.set_field_at(index=1, name=f"{get_emoji(owoweekly)} OwO Weekly Leaderboard", value=f"{'Enabled' if owoweekly else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[2]:
                votelb = await self.handle_toggle(ctx.guild, 'votelb')
                embed.set_field_at(index=2, name=f"{get_emoji(votelb)} Vote Leaderboard", value=f"{'Enabled' if votelb else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[3]:
                tempembed = discord.Embed(title='Information', color=self.client.embed_color, description="React with the emojis to toggle leaderboards")
                tempembed.add_field(name='Reactions' ,value=f"{emojis[0]} Toggles OwO daily leaderboard\n{emojis[1]} Toggles OwO weekly leaderboard\n{emojis[2]} Toggles vote leaderboard\n{emojis[3]} Shows this infomation message.")
                await message.edit(embed=tempembed)
            await message.remove_reaction(response.emoji, ctx.author)