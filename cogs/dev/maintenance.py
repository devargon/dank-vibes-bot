import discord
from utils import checks
from datetime import datetime
from discord.ext import commands

class Maintenance(commands.Cog):
    def __init__(self, client):
        self.client = client

    def get_emoji(self, enabled):
        if enabled:
            return "<:DVB_enabled:872003679895560193>"
        return "<:DVB_disabled:872003709096321024>"

    def get_maintenance_embed(self):
        embed = discord.Embed(color=self.client.embed_color, title="Maintenance List", timestamp=datetime.utcnow())
        for name in sorted(list(self.client.cogs.keys())):
            enabled = self.client.maintenance.get(name)
            embed.add_field(name=f"{self.get_emoji(enabled)} {name.capitalize()}", value='Under maintenance' if enabled else 'Active', inline=True)
        return embed

    @checks.dev()
    @commands.group(name='maintenance', invoke_without_command=True)
    async def maintenance(self, ctx):
        """
        Base command for managing bot's maintenance mode.
        """
        embed = self.get_maintenance_embed()
        await ctx.send(embed=embed)
        
    @maintenance.command(name='on', aliases=['enable'], usage="<cogs>")
    async def maintenance_on(self, ctx, *, cogs: str = None):
        """
        Enables maintenance mode on a cog.
        """
        if cogs is None:
            return await ctx.send("Specify an extension")
        _cogs = []
        if cogs.lower() in ['all', '*']:
            _cogs = [self.client.get_cog(cog) for cog in sorted(list(self.client.cogs.keys()))]
        else:
            cog_names = [cog.strip() for cog in cogs.rsplit(',' if ',' in cogs else ' ')]
            for cog_name in cog_names:
                if not (cog := self.client.get_cog(cog_name)):
                    return await ctx.send(f"{cog_name} is not a valid extension.")
                _cogs.append(cog)
        values = []
        for cog in _cogs:
            if self.client.maintenance.get(cog.qualified_name):
                continue
            values.append((cog.qualified_name, True))
            self.client.maintenance[cog.qualified_name] = True
        await self.client.pool_pg.executemany("UPDATE maintenance SET enabled=$2 WHERE cog_name=$1", values)
        embed = self.get_maintenance_embed()
        await ctx.send(embed=embed)
        
    @maintenance.command(name='off', aliases=['disable'], usage="<cogs>")
    async def maintenance_off(self, ctx, *, cogs: str = None):
        """
        Disables maintenance mode on a cog.
        """
        if cogs is None:
            return await ctx.send("Specify an extension")
        _cogs = []
        if cogs.lower() in ['all', '*']:
            _cogs = [self.client.get_cog(cog) for cog in sorted(list(self.client.cogs.keys()))]
        else:
            cog_names = [cog.strip() for cog in cogs.rsplit(',' if ',' in cogs else ' ')]
            for cog_name in cog_names:
                if not (cog := self.client.get_cog(cog_name)):
                    return await ctx.send(f"{cog_name} is not a valid extension.")
                _cogs.append(cog)
        values = []
        for cog in _cogs:
            if not self.client.maintenance.get(cog.qualified_name):
                continue
            values.append((cog.qualified_name, False))
            self.client.maintenance[cog.qualified_name] = False
        await self.client.pool_pg.executemany("UPDATE maintenance SET enabled=$2 WHERE cog_name=$1", values)
        embed = self.get_maintenance_embed()
        await ctx.send(embed=embed)
    
    @maintenance.command(name='message', usage='<cog> <message>')
    async def maintenance_message(self, ctx, cog_name: str = None, *, message: str = None):
        """
        Sets the maintenance message.
        """
        query = "UPDATE maintenance SET message=$2 WHERE cog_name=$1"
        if cog_name is None:
            return await ctx.send("Specify an extension")
        if cog_name.lower() in ['all', '*']:
            if message is None:
                embed = discord.Embed(title="Maintenance Messages", color=self.client.embed_color, timestamp=datetime.utcnow())
                for name in sorted(list(self.client.cogs.keys())):
                    enabled = self.client.maintenance.get(name)
                    embed.add_field(name=f"{self.get_emoji(enabled)} {name.capitalize()}", value=self.client.maintenance_message.get(name), inline=True)
                return await ctx.send(embed=embed)
            values = []
            for name in sorted(list(self.client.cogs.keys())):
                self.client.maintenance_message[name] = message
                values.append(name, message)
            await self.client.pool_pg.executemany(query, values)
        else:
            if not (cog := self.client.get_cog(cog_name)):
                return await ctx.send(f"{cog_name} is not a valid extension.")
            if message is None:
                embed = discord.Embed(title="Maintenance Message", color=self.client.embed_color, timestamp=datetime.utcnow())
                enabled = self.client.get(cog.qualified_name)
                embed.add_field(name=f"{self.get_emoji(enabled)} {cog.qualified_name.capitalize()}", value=self.client.maintenance_message.get(cog.qualified_name), inline=True)
                return await ctx.send(embed=embed)
            value = (cog.qualified_name, message)
            await self.client.pool_pg.execute(query, value)
            self.client.maintenance_message[cog.qualified_name] = message
        return await ctx.checkmark()