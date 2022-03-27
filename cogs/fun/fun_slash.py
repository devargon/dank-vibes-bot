import discord
from discord import Webhook, Option
from discord.ext import commands
import aiohttp
from utils import checks


class FunSlash(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.perm_insensitive_roles()
    @commands.slash_command(name="hideping", description="Secretly ping someone with this command!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hideping_slash(self, ctx,
                             target: Option(discord.Member, "Who you want to ping"),
                             channel: Option(discord.TextChannel,
                                             "If you want to ping someone in another channel") = None,
                             message: Option(str, "An optional message") = None
                             ):
        if channel is None:
            channel = ctx.channel
        if not (channel.permissions_for(ctx.author).send_messages and channel.permissions_for(ctx.author).view_channel):
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond("You are not authorized to view/send messages in that channel.", ephemeral=True)
        if message is not None and len(message) > 180:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(f"Your accompanying message is currently {len(message)} characters long; it can only be at most 180 characters.", ephemeral=True)
        if message is None:
            message = ''
        if await self.client.check_blacklisted_content(message):
            message = ''
        content = f"{message or ''} ‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍ <@{target.id}>"  # ik this looks sketchy, but you can paste it in discord and send it to see how this looks like :MochaLaugh:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=self.client.user.name)
        if webhook is None:
            try:
                webhook = await channel.create_webhook(name=self.client.user.name)
            except discord.Forbidden:
                try:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.respond("I am unable to create a webhook to send the hideping message.", ephemeral=True)
                except (discord.HTTPException, discord.Forbidden):
                    ctx.command.reset_cooldown(ctx)
                    return
                return
        await webhook.send(content, username="You were hidepinged",
                           avatar_url="https://cdn.discordapp.com/attachments/871737314831908974/895639630429433906/incognito.png")
        await ctx.respond(f"**{target}** has been secretly pinged in {channel.mention}! <:qbgiggle:718020317632790548>",
                          ephemeral=True)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                'https://canary.discord.com/api/webhooks/883563427455438858/GsF8ZPIemw6D-x6TIp7wO88ySQizKePKCS5zRA-EBtNfHRC15e9koti7-02GKBuoZ_Yi',
                session=session)
            embed = discord.Embed(title=f"Hideping command invoked with {ctx.me}", color=discord.Color.green())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Target", value=f"**{target}** ({target.id})", inline=True)
            embed.add_field(name="Message", value=message or "No message", inline=True)
            await webhook.send(embed=embed, username=f"{self.client.user.name} Logs")

    @commands.slash_command(name="dm", description="Acting like a messenger, Dank Vibes Bot anonymously will DM the user on your behalf.")
    @checks.perm_insensitive_roles()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def dm_slash(self, ctx: discord.ApplicationContext,
                       member: discord.Option(discord.Member, "The user you want to send a message to"),
                       message: discord.Option(str, "What to DM to the user")
                       ):
        if member.id == self.client.user.id:
            return await ctx.respond("Just DM me already... Do you not know how to DM me??\nhttps://cdn.nogra.me/core/how_to_dm_a_bot.gif", ephemeral=True)
        if member.bot:
            return await ctx.respond(f"🤖 **{member}**: `Do not speak to me, you inferior human being.`", ephemeral=True)
        if len(message) > 4000:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(f"Your message has {len(message)} characters. It can only have a maximum of 4000 characters.", ephemeral=True)
        if await self.client.check_blacklisted_content(message):
            return await ctx.respond("You cannot send content with blacklisted words via the bot.", ephemeral=True)
        if not (config := self.dmconfig.get(ctx.guild.id)):
            config = await self.client.pool_pg.fetchrow("SELECT dmchannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('dmchannel_id') is None:
                return await ctx.respond('This server has not set a channel for DM requests to be directed to. Have someone with the `Administrator` Permission to add a DM request channel with `dv.setdmchannel <channel>`.', ephemeral=True)
            config = self.dmconfig.setdefault(ctx.guild.id, config.get('dmchannel_id'))
        request_channel = ctx.guild.get_channel(config)
        if request_channel is None:
            await self.client.pool_pg.execute("DELETE FROM channelconfigs WHERE guild_id = $1", ctx.guild.id, ephemeral=True)
            return await ctx.respond("I could not find the channel to send DM requests to. Please contact an admin about this!", ephemeral=True)
        existing = await self.client.pool_pg.fetch("SELECT * FROM dmrequests WHERE member_id = $1 and target_id = $2 and dmcontent = $3", ctx.author.id, member.id, message)
        if len(existing) > 0:
            return await ctx.respond("I already have an existing DM request that matches your new request.", ephemeral=True)
        await self.client.pool_pg.execute("INSERT INTO dmrequests(member_id, target_id, dmcontent) values($1, $2, $3)", ctx.author.id, member.id, message)
        ID = (await self.client.pool_pg.fetchrow("SELECT id FROM dmrequests where member_id = $1 and dmcontent = $2", ctx.author.id, message)).get('id')
        embed = discord.Embed(title="DM Request", description=message, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="DM Target", value=f"{member} {member.mention}")
        embed.add_field(name="Status", value="Not approved", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon.url)
        view = DMPersistentView(self.client)
        new_message = await request_channel.send(embed=embed, view=view)
        await self.client.pool_pg.execute("UPDATE dmrequests set messageid = $1 where id = $2", new_message.id, ID)
        authorembed = discord.Embed(title="Your DM request has been submitted!", description="I will notify you on the status of your DM request.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        authorembed.set_author(icon_url=ctx.guild.icon.url, name=ctx.guild.name)
        authorembed.add_field(name="Message", value=(message[:1020] + '...') if len(message) > 1024 else message, inline=False)
        authorembed.add_field(name="DM Target", value=f"{member} {member.mention}", inline=True)
        authorembed.add_field(name="Request ID", value=str(ID), inline=True)
        authorembed.set_footer(text="Your DM request will be denied if it breaks server rules.")
        try:
            await ctx.author.send(embed=authorembed)
        except discord.Forbidden:
            await ctx.respond("Your DM request has been submitted!", embed=authorembed, ephemeral=True)
        else:
            await ctx.respond("Your DM request has been submitted, check your DMs!", ephemeral=True)