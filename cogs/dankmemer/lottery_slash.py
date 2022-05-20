import discord
from discord import SlashCommandGroup
from discord.ext import commands
from main import dvvt
from utils import checks
from utils.buttons import confirm


class LotterySlash(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    lottery_group = SlashCommandGroup("lottery", "Lottery Management Commands")

    @checks.has_permissions_or_role(manage_roles=True)
    @lottery_group.command(name='start')
    async def lottery_slash_start(self, ctx: discord.ApplicationContext,
                                  type: discord.Option(str, description="The type of lottery.",
                                                       choices=['dank', 'karuta', 'owo']),
                                  max_tickets: discord.Option(int, description="The maximum number of tickets."),
                                  entry_fee: discord.Option(str, description="The entry fee.")
                                  ):
        embed = discord.Embed(title=entry_fee,
                              description=f"Holder: {ctx.author.mention}\nChannel: <#680002065950703646>\nMaximum Entries: `{max_tickets}`",
                              color=self.client.embed_color)
        if type == 'owo':
            embed.add_field(name="Entry:", value=f"<a:dv_pointArrowOwO:837656328482062336> Give {ctx.author.mention} `{entry_fee}` in <#859761515761762304> to enter!")
        elif type == 'dank':
            embed.add_field(name="Entry:", value=f"<a:dv_pointArrowOwO:837656328482062336> Read the sticky message in <#680002065950703646> for information on how to enter!")
        elif type == 'karuta':
            embed.add_field(name="Entry:", value=f"<a:dv_pointArrowOwO:837656328482062336> Follow the format given in <#887006001566462062> and kindly wait for a <@&843756047964831765> to assist you!")
        if ctx.guild.id == 595457764935991326:
            if type == 'dank':
                ping = "<@&680131933778346011>"
            elif type == 'owo':
                ping = "<@&847538763412668456>"
            elif type == 'karuta':
                ping = "<@&886983702402457641>"
            else:
                ping = None
        else:
            if type == 'dank':
                ping = "<@&895815799812521994>"
            elif type == 'owo':
                ping = "<@&955387105373204490>"
            elif type == 'karuta':
                ping = "<@&976662248787415060>"
            else:
                ping = None
        dank_required_roles = [663502776952815626, 684591962094829569, 608500355973644299]
        karuta_required_roles = [843756047964831765, 663502776952815626, 684591962094829569, 608500355973644299]
        owo_required_roles = [837595910661603330, 663502776952815626, 684591962094829569, 608500355973644299]
        if ctx.guild.id == 595457764935991326:
            if type == 'dank':
                if not any([ctx.guild.get_role(r_id) in ctx.author.roles for r_id in dank_required_roles]):
                    confirm_host_view = confirm(ctx, self.client, 30.0)
                else:
                    confirm_host_view = None
            elif type == 'karuta':
                if not any([ctx.guild.get_role(r_id) in ctx.author.roles for r_id in karuta_required_roles]):
                    confirm_host_view = confirm(ctx, self.client, 30.0)
                else:
                    confirm_host_view = None
            elif type == 'owo':
                if not any([ctx.guild.get_role(r_id) in ctx.author.roles for r_id in owo_required_roles]):
                    confirm_host_view = confirm(ctx, self.client, 30.0)
                else:
                    confirm_host_view = None
            else:
                confirm_host_view = None
            if confirm_host_view:
                confirm_host_embed = discord.Embed(title="It doesn't seem like you're a staff for this category.",
                                                   description=f"Are you sure you want to start a lottery for the `{type}` category?",
                                                   color=discord.Color.orange())
                confirm_host_view.response = await ctx.respond(embed=confirm_host_embed, view=confirm_host_view, ephemeral=True)
                await confirm_host_view.wait()
                if confirm_host_view.returning_value is not True:
                    return
        confirm_start_view = confirm(ctx, self.client, 30.0)
        confirm_start_embed = discord.Embed(title=f"Ready to start a {type} lottery?",
                                            description=f"Holder: {ctx.author.mention}\nChannel: <#680002065950703646>\nMaximum Entries: `{max_tickets}`",
                                            color=self.client.embed_color)
        confirm_start_view.response = await ctx.respond(embed=confirm_start_embed, view=confirm_start_view, ephemeral=True)
        await confirm_start_view.wait()
        if confirm_start_view.returning_value is not True:
            return
        lottery_id = await self.client.db.fetchval("INSERT INTO lotteries(lottery_type, guild_id, starter_id, lottery_entry) VALUES($1, $2, $3, $4) RETURNING lottery_id", type, ctx.guild.id, ctx.author.id, entry_fee, column='lottery_id')
        embed.set_footer(text=f"Lottery #{lottery_id} • {ctx.guild.name}")
        await ctx.respond(ping, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True, everyone=False))

    @checks.has_permissions_or_role(manage_roles=True)
    @lottery_group.command(name="reserve")
    async def lottery_reserve(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member), count: discord.Option(int)):
        pass

    @checks.has_permissions_or_role(manage_roles=True)
    @lottery_group.command(name="makecount")
    async def lottery_makecount(self, ctx: discord.ApplicationContext, count: discord.Option(int)):

        pass

    @checks.has_permissions_or_role(manage_roles=True)
    @lottery_group.command(name='end')
    async def lottery_end(self, ctx: discord.ApplicationContext):
        pass
