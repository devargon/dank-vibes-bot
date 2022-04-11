import asyncio
import json
import random
import time

import discord
from discord import Webhook, Option
from discord.ext import commands
import aiohttp
from utils import checks


def lowered_cooldown(message: discord.Message):
    if discord.utils.get(message.author.roles, id=874833402052878396):  # Contributor 24T
        return commands.Cooldown(1, 900)
    elif discord.utils.get(message.author.roles, id=931174008970444800):  # weekly top grinder
        return commands.Cooldown(1, 900)
    elif discord.utils.get(message.author.roles, name="Vibing Investor"):
        return commands.Cooldown(1, 1800)
    else:
        return commands.Cooldown(1, 3600)

class DMPersistentView(discord.ui.View):
    def __init__(self, client):
        self.client = client
        super().__init__(timeout=None)

    @discord.ui.button(label='Approve', emoji=discord.PartialEmoji.from_str("<:DVB_checkmark:955345523139805214>"), style=discord.ButtonStyle.green, custom_id="button:approve_dm") #, custom_id='persistent_view:approve')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        dm_request = await self.client.db.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", interaction.message.id)
        if dm_request is None:
            return
        dmrequester = interaction.guild.get_member(dm_request.get('member_id'))
        if dmrequester is None:
            authordetails = dm_request.get('member_id')
        else:
            authordetails = f"{dmrequester} ({dmrequester.id})"
        dmtarget = interaction.guild.get_member(dm_request.get('target_id'))
        ID = dm_request.get('id')
        dmcontent = dm_request.get('dmcontent')
        approver = interaction.guild.get_member(interaction.user.id)
        if not approver.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have the required permissions to approve this request.", ephemeral=True)
        if dmrequester is None:
            output = (1, "Failed: User who requested the DM has left the server",)
        elif dmtarget is None:
            output = (1, "Failed: Targetted user to DM has left the server",)
        else:
            try:
                await dmtarget.send(embed=discord.Embed(title="You have received an anonymous message!", description=dmcontent, color=self.client.embed_color))
            except discord.Forbidden:
                output = (1, "Failed: Unable to DM user",)
            else:
                output = (2, "Approved DM sent",)
        await self.client.db.execute("DELETE from dmrequests WHERE id = $1", ID)
        await self.client.db.execute("INSERT INTO dmrequestslog values($1, $2, $3, $4, $5, $6)", ID, dmrequester.id if dmrequester else dm_request.get('member_id'), dmtarget.id if dmtarget else dm_request.get('target_id'), interaction.user.id, dmcontent, output[0]) # 0 : Denied, 1: Failed, 2 : Approved
        embed = discord.Embed(title="DM Request", description = dmcontent, color=discord.Color.green() if output[0] == 2 else discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=authordetails)
        dmtargetdetails = f"{dmtarget} {dmtarget.mention}" if dmtarget is not None else dmtarget
        embed.add_field(name="DM Target", value=f"{dmtargetdetails}")
        embed.add_field(name="Status", value=output[1], inline=True)
        if dmrequester is not None:
            embed.set_thumbnail(url=dmrequester.display_avatar.url)
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        for b in self.children:
            b.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        if output[0] == 1:
            if output[1] == "Failed: Member has left the server" or output[0] not in [1, 2, 0]:
                msgcontent = None
            elif output[1] == "Failed: Targetted user to DM has left the server":
                msgcontent = "The user who you attempted to send an anonymous DM has left the server. Sorry about that!"
            elif output[1] == "Failed: Unable to DM user":
                msgcontent = f"I am unable to DM {dmtarget}. Sorry about that!"
            else:
                msgcontent = None
        elif output[0] == 2:
            msgcontent = f"Your message was successfully sent to {dmtarget}!"
        else:
            msgcontent = f"Your DM request was denied."
        if msgcontent is not None and dmrequester is not None:
            try:
                await dmrequester.send(msgcontent)
            except discord.Forbidden:
                pass
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @discord.ui.button(label='Deny', emoji=discord.PartialEmoji.from_str("<:DVB_crossmark:955345521151737896>"), style=discord.ButtonStyle.red, custom_id="button:deny_dm") #c, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        dm_request = await self.client.db.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", interaction.message.id)
        if dm_request is None:
            return
        dmrequester = interaction.guild.get_member(dm_request.get('member_id'))
        if dmrequester is None:
            authordetails = dm_request.get('member_id')
        else:
            authordetails = f"{dmrequester} ({dmrequester.id})"
        dmtarget = interaction.guild.get_member(dm_request.get('target_id'))
        ID = dm_request.get('id')
        dmcontent = dm_request.get('dmcontent')
        approver = interaction.guild.get_member(interaction.user.id)
        if not approver.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have the required permissions to approve this request.", ephemeral=True)
        if dmrequester is None:
            output = (1, "Failed: User who requested the DM has left the server",)
        else:
            output = (0, "Denied")
        await self.client.db.execute("DELETE from dmrequests WHERE id = $1", ID)
        await self.client.db.execute("INSERT INTO dmrequestslog values($1, $2, $3, $4, $5, $6)", ID, dmrequester.id if dmrequester else dm_request.get('member_id'), dmtarget.id if dmtarget else dm_request.get('target_id'), interaction.user.id, dmcontent, output[0]) # 0 : Denied, 1: Failed, 2 : Approved
        embed = discord.Embed(title="DM Request", description = dmcontent, color=discord.Color.green() if output[0] == 2 else discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=authordetails)
        dmtargetdetails = f"{dmtarget} {dmtarget.mention}" if dmtarget is not None else dmtarget
        embed.add_field(name="DM Target", value=f"{dmtargetdetails}")
        embed.add_field(name="Status", value=output[1], inline=True)
        if dmrequester is not None:
            embed.set_thumbnail(url=dmrequester.display_avatar.url)
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        for b in self.children:
            b.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        if output[0] == 1:
            msgcontent = None
        else:
            msgcontent = f"Your DM request was denied."
        if msgcontent is not None and dmrequester is not None:
            try:
                await dmrequester.send(msgcontent)
            except discord.Forbidden:
                pass
        await asyncio.sleep(10)
        await interaction.delete_original_message()

class FunSlash(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open('assets/localization/dumbfight_statements.json', 'r') as f:
            self.dumbfight_statements = json.load(f)

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
            config = await self.client.db.fetchrow("SELECT dmchannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('dmchannel_id') is None:
                return await ctx.respond('This server has not set a channel for DM requests to be directed to. Have someone with the `Administrator` Permission to add a DM request channel with `dv.setdmchannel <channel>`.', ephemeral=True)
            config = self.dmconfig.setdefault(ctx.guild.id, config.get('dmchannel_id'))
        request_channel = ctx.guild.get_channel(config)
        if request_channel is None:
            await self.client.db.execute("DELETE FROM channelconfigs WHERE guild_id = $1", ctx.guild.id, ephemeral=True)
            return await ctx.respond("I could not find the channel to send DM requests to. Please contact an admin about this!", ephemeral=True)
        existing = await self.client.db.fetch("SELECT * FROM dmrequests WHERE member_id = $1 and target_id = $2 and dmcontent = $3", ctx.author.id, member.id, message)
        if len(existing) > 0:
            return await ctx.respond("I already have an existing DM request that matches your new request.", ephemeral=True)
        await self.client.db.execute("INSERT INTO dmrequests(member_id, target_id, dmcontent) values($1, $2, $3)", ctx.author.id, member.id, message)
        ID = (await self.client.db.fetchrow("SELECT id FROM dmrequests where member_id = $1 and dmcontent = $2", ctx.author.id, message)).get('id')
        embed = discord.Embed(title="DM Request", description=message, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="DM Target", value=f"{member} {member.mention}")
        embed.add_field(name="Status", value="Not approved", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon.url)
        view = DMPersistentView(self.client)
        new_message = await request_channel.send(embed=embed, view=view)
        await self.client.db.execute("UPDATE dmrequests set messageid = $1 where id = $2", new_message.id, ID)
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

    @checks.perm_insensitive_roles()
    @commands.dynamic_cooldown(lowered_cooldown, commands.BucketType.user)
    @commands.slash_command(name="dumbfight", name_localizations={
        "da": "k\u00e6mpe",
        "de": "k\u00e4mpfen",
        "es-ES": "pelear",
        "fr": "lutte",
        "hr": "borba",
        "it": "combattimento",
        "lt": "kovoti",
        "hu": "harc",
        "nl": "gevecht",
        "no": "sl\u00e5ss",
        "pl": "walka",
        "pt-BR": "lutar",
        "ro": "lupt\u0103",
        "fi": "taistella",
        "sv-SE": "bek\u00e4mpa",
        "vi": "đ\u00e1nh_nhau",
        "tr": "kavga_etmek",
        "cs": "pr\u00e1t_se",
        "el": "\u03c0\u03ac\u03bb\u03b7",
        "bg": "\u0431\u0438\u0442\u043a\u0430",
        "ru": "\u0431\u043e\u0440\u044c\u0431\u0430",
        "uk": "\u0431\u043e\u0440\u043e\u0442\u0438\u0441\u044f", #hindi and thai removed
        "zh-CN": "打架",
        "ja": "\u55a7\u5629",
        "zh-TW": "打架",
        "ko": "\uc2f8\uc6c0"
    }, description="Mute people for a random duration between 30 to 120 seconds.", description_localizations={
        "da": "Sl\u00e5 lyden fra for personer i en tilf\u00e6ldig varighed mellem 30 og 120 sekunder.",
        "de": "Schalten Sie Personen f\u00fcr eine zuf\u00e4llige Dauer zwischen 30 und 120 Sekunden stumm.",
        "es-ES": "Silencie a las personas por una duraci\u00f3n aleatoria de entre 30 y 120 segundos.",
        "fr": "D\u00e9sactiver les personnes pendant une dur\u00e9e al\u00e9atoire comprise entre 30 et 120 secondes.",
        "hr": "Isklju\u010dite ljude na nasumi\u010dno trajanje izme\u0111u 30 i 120 sekundi.",
        "it": "Disattiva l'audio delle persone per una durata casuale compresa tra 30 e 120 secondi.",
        "lt": "Nutildykite \u017emones atsitiktinai nuo 30 iki 120 sekund\u017ei\u0173.",
        "hu": "N\u00e9m\u00edtsa el az embereket v\u00e9letlenszer\u0171en, 30 \u00e9s 120 m\u00e1sodperc k\u00f6z\u00f6tt.",
        "nl": "Demp mensen voor een willekeurige duur tussen 30 en 120 seconden.",
        "no": "Demp folk i en tilfeldig varighet mellom 30 og 120 sekunder.",
        "pl": "Wycisz ludzi na losowy czas od 30 do 120 sekund.",
        "pt-BR": "Silencie as pessoas por uma dura\u00e7\u00e3o aleat\u00f3ria entre 30 a 120 segundos.",
        "ro": "Dezactiva\u021bi sunetul persoanelor pentru o durat\u0103 aleatorie \u00eentre 30 \u0219i 120 de secunde.",
        "fi": "Mykist\u00e4 ihmiset satunnaisesti 30\u2013120 sekunnin ajaksi.",
        "sv-SE": "St\u00e4ng av ljudet f\u00f6r personer under en slumpm\u00e4ssig varaktighet mellan 30 och 120 sekunder.",
        "vi": "T\u1eaft ti\u1ebfng m\u1ecdi ng\u01b0\u1eddi trong kho\u1ea3ng th\u1eddi gian ng\u1eabu nhi\u00ean t\u1eeb 30 \u0111\u1ebfn 120 gi\u00e2y.",
        "tr": "\u0130nsanlar\u0131 30 ila 120 saniye aras\u0131nda rastgele bir s\u00fcre boyunca sessize al\u0131n.",
        "cs": "Ztlumit lidi na n\u00e1hodnou dobu mezi 30 a\u017e 120 sekundami.",
        "el": "\u03a3\u03af\u03b3\u03b1\u03c3\u03b7 \u03b1\u03c4\u03cc\u03bc\u03c9\u03bd \u03b3\u03b9\u03b1 \u03c4\u03c5\u03c7\u03b1\u03af\u03b1 \u03b4\u03b9\u03ac\u03c1\u03ba\u03b5\u03b9\u03b1 \u03b1\u03c0\u03cc 30 \u03ad\u03c9\u03c2 120 \u03b4\u03b5\u03c5\u03c4\u03b5\u03c1\u03cc\u03bb\u03b5\u03c0\u03c4\u03b1.",
        "bg": "\u0417\u0430\u0433\u043b\u0443\u0448\u0430\u0432\u0430\u0439\u0442\u0435 \u0445\u043e\u0440\u0430\u0442\u0430 \u0437\u0430 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u043b\u043d\u0430 \u043f\u0440\u043e\u0434\u044a\u043b\u0436\u0438\u0442\u0435\u043b\u043d\u043e\u0441\u0442 \u043c\u0435\u0436\u0434\u0443 30 \u0438 120 \u0441\u0435\u043a\u0443\u043d\u0434\u0438.",
        "ru": "\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 \u0437\u0432\u0443\u043a\u0430 \u043b\u044e\u0434\u0435\u0439 \u043d\u0430 \u0441\u043b\u0443\u0447\u0430\u0439\u043d\u044b\u0439 \u043f\u0435\u0440\u0438\u043e\u0434 \u0432\u0440\u0435\u043c\u0435\u043d\u0438 \u043e\u0442 30 \u0434\u043e 120 \u0441\u0435\u043a\u0443\u043d\u0434.",
        "uk": "\u0412\u0438\u043c\u043a\u043d\u0456\u0442\u044c \u043b\u044e\u0434\u0435\u0439 \u043d\u0430 \u0434\u043e\u0432\u0456\u043b\u044c\u043d\u0438\u0439 \u0447\u0430\u0441 \u0432\u0456\u0434 30 \u0434\u043e 120 \u0441\u0435\u043a\u0443\u043d\u0434.",
        "hi": "30 \u0938\u0947 120 \u0938\u0947\u0915\u0902\u0921 \u0915\u0947 \u092c\u0940\u091a \u092f\u093e\u0926\u0943\u091a\u094d\u091b\u093f\u0915 \u0905\u0935\u0927\u093f \u0915\u0947 \u0932\u093f\u090f \u0932\u094b\u0917\u094b\u0902 \u0915\u094b \u092e\u094d\u092f\u0942\u091f \u0915\u0930\u0947\u0902\u0964",
        "th": "\u0e1b\u0e34\u0e14\u0e40\u0e2a\u0e35\u0e22\u0e07\u0e1c\u0e39\u0e49\u0e04\u0e19\u0e40\u0e1b\u0e47\u0e19\u0e23\u0e30\u0e22\u0e30\u0e40\u0e27\u0e25\u0e32\u0e41\u0e1a\u0e1a\u0e2a\u0e38\u0e48\u0e21\u0e23\u0e30\u0e2b\u0e27\u0e48\u0e32\u0e07 30 \u0e16\u0e36\u0e07 120 \u0e27\u0e34\u0e19\u0e32\u0e17\u0e35",
        "zh-CN": "\u5c06\u4eba\u9759\u97f3 30 \u5230 120 \u79d2\u4e4b\u95f4\u7684\u968f\u673a\u6301\u7eed\u65f6\u95f4\u3002",
        "ja": "30\u301c120\u79d2\u306e\u30e9\u30f3\u30c0\u30e0\u306a\u6642\u9593\u3067\u4eba\u3092\u30df\u30e5\u30fc\u30c8\u3057\u307e\u3059\u3002",
        "zh-TW": "\u5c07\u4eba\u975c\u97f3 30 \u5230 120 \u79d2\u4e4b\u9593\u7684\u96a8\u6a5f\u6301\u7e8c\u6642\u9593\u3002",
        "ko": "30\ucd08\uc5d0\uc11c 120\ucd08 \uc0ac\uc774\uc758 \uc784\uc758\uc758 \uc2dc\uac04 \ub3d9\uc548 \uc0ac\ub78c\ub4e4\uc744 \uc74c\uc18c\uac70\ud569\ub2c8\ub2e4."
    }, guild_ids = [871734809154707467, 595457764935991326])
    async def dumbfight_slash(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, name="target", name_localizations={
        "en-GB": "target",
        "en-US": "target",
        "da": "m\u00e5l",
        "de": "ziel",
        "es-ES": "objetivo",
        "fr": "cibler",
        "hr": "cilj",
        "it": "bersaglio",
        "lt": "taikinys",
        "hu": "c\u00e9l",
        "nl": "doel",
        "no": "m\u00e5l",
        "pl": "cel",
        "pt-BR": "alvo",
        "ro": "\u0163int\u0103",
        "fi": "kohde",
        "sv-SE": "m\u00e5l",
        "vi": "m\u1ee5c_ti\u00eau",
        "tr": "hedef",
        "cs": "c\u00edlov\u00e1",
        "el": "\u03c3\u03c4\u03cc\u03c7\u03bf\u03c2",
        "bg": "\u0446\u0435\u043b",
        "ru": "\u0446\u0435\u043b\u044c",
        "uk": "\u0446\u0456\u043b\u044c",
        "hi": "target",
        "th": "\u0e40\u0e1b\u0e49\u0e32",
        "zh-CN": "\u76ee\u6807",
        "ja": "\u76ee\u6a19",
        "zh-TW": "\u76ee\u6a19",
        "ko": "\ud45c\uc801"
    },
                                                                                            description="The person you want to fight", description_localizations={
        "en-GB": "The person that you want to fight with.",
        "en-US": "The person that you want to fight with.",
        "da": "Den person, du vil sl\u00e5s med.",
        "de": "Die Person, mit der Sie k\u00e4mpfen m\u00f6chten.",
        "es-ES": "La persona con la que quieres pelear.",
        "fr": "La personne avec qui tu veux te battre.",
        "hr": "Osoba s kojom se \u017eelite boriti.",
        "it": "La persona con cui vuoi combattere.",
        "lt": "\u017dmogus, su kuriuo norite kovoti.",
        "hu": "Az a szem\u00e9ly, akivel harcolni akarsz.",
        "nl": "De persoon met wie je wilt vechten.",
        "no": "Personen du vil sl\u00e5ss med.",
        "pl": "Osoba, z kt\u00f3r\u0105 chcesz walczy\u0107.",
        "pt-BR": "A pessoa com quem voc\u00ea quer lutar.",
        "ro": "Persoana cu care vrei s\u0103 te lup\u021bi.",
        "fi": "Henkil\u00f6, jonka kanssa haluat taistella.",
        "sv-SE": "Personen du vill sl\u00e5ss med.",
        "vi": "Ng\u01b0\u1eddi m\u00e0 b\u1ea1n mu\u1ed1n chi\u1ebfn \u0111\u1ea5u c\u00f9ng.",
        "tr": "Kavga etmek istedi\u011fin ki\u015fi.",
        "cs": "Osoba, se kterou chcete bojovat.",
        "el": "\u03a4\u03bf \u03ac\u03c4\u03bf\u03bc\u03bf \u03bc\u03b5 \u03c4\u03bf \u03bf\u03c0\u03bf\u03af\u03bf \u03b8\u03ad\u03bb\u03b5\u03c4\u03b5 \u03bd\u03b1 \u03c4\u03c3\u03b1\u03ba\u03c9\u03b8\u03b5\u03af\u03c4\u03b5.",
        "bg": "\u0427\u043e\u0432\u0435\u043a\u044a\u0442, \u0441 \u043a\u043e\u0433\u043e\u0442\u043e \u0438\u0441\u043a\u0430\u0442\u0435 \u0434\u0430 \u0441\u0435 \u0431\u0438\u0435\u0442\u0435.",
        "ru": "\u0427\u0435\u043b\u043e\u0432\u0435\u043a, \u0441 \u043a\u043e\u0442\u043e\u0440\u044b\u043c \u0432\u044b \u0445\u043e\u0442\u0438\u0442\u0435 \u043f\u043e\u0434\u0440\u0430\u0442\u044c\u0441\u044f.",
        "uk": "\u041b\u044e\u0434\u0438\u043d\u0430, \u0437 \u044f\u043a\u043e\u044e \u0442\u0438 \u0445\u043e\u0447\u0435\u0448 \u0431\u0438\u0442\u0438\u0441\u044f.",
        "hi": "\u091c\u093f\u0938 \u0935\u094d\u092f\u0915\u094d\u0924\u093f \u0938\u0947 \u0906\u092a \u0932\u0921\u093c\u0928\u093e \u091a\u093e\u0939\u0924\u0947 \u0939\u0948\u0902\u0964",
        "th": "\u0e04\u0e19\u0e17\u0e35\u0e48\u0e04\u0e38\u0e13\u0e2d\u0e22\u0e32\u0e01\u0e15\u0e48\u0e2d\u0e2a\u0e39\u0e49\u0e14\u0e49\u0e27\u0e22",
        "zh-CN": "\u4f60\u60f3\u4e0e\u4e4b\u6218\u6597\u7684\u4eba\u3002",
        "ja": "\u6226\u3044\u305f\u3044\u76f8\u624b\u3002",
        "zh-TW": "\u4f60\u60f3\u8207\u4e4b\u6230\u9b25\u7684\u4eba\u3002",
        "ko": "\ub2f9\uc2e0\uc774 \uc2f8\uc6b0\uace0 \uc2f6\uc740 \uc0ac\ub78c."
    })):
        with open('assets/localization/dumbfight_content.json', 'r') as f:
            responses = json.load(f)

        def get_statement(statement: dict):
            return statement.get(ctx.interaction.locale, statement['en-US'])

        if self.gen_is_muted and ctx.channel.id == 608498967474601995:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(get_statement(responses[0]), ephemeral=True)
        if ctx.channel.id in self.mutedusers and member.id in self.mutedusers[ctx.channel.id]:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(get_statement(responses[1]).format(member.name), ephemeral=True)
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(get_statement(responses[2]), ephemeral=True)
        if member == ctx.me:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(get_statement(responses[3]), ephemeral=True)
        duration = random.randint(30, 120)
        won_dumbfights = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 1, ctx.author.id)
        lost_dumbfights = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 0, ctx.author.id)
        try:
            wonlossratio = len(won_dumbfights) / len(lost_dumbfights)
        except ZeroDivisionError:
            doesauthorwin = random.choice([True, False])
        else:
            if wonlossratio == 0 or wonlossratio >= 0.7 and wonlossratio <= 1.5:
                doesauthorwin = random.choice([True, False])
            elif wonlossratio < 0.7:
                doesauthorwin = True
            else:
                doesauthorwin = False
        author_df_details = await self.client.db.fetchrow("SELECT dumbfight_result, dumbfight_rig_duration FROM userconfig WHERE user_id = $1", ctx.author.id)
        if author_df_details is not None and author_df_details.get('dumbfight_rig_duration') is not None and author_df_details.get('dumbfight_rig_duration') > round(time.time()):
            author_has_shield_potion = author_df_details.get('dumbfight_result')
        else:
            author_has_shield_potion = None
        target_df_details = await self.client.db.fetchrow("SELECT dumbfight_result, dumbfight_rig_duration FROM userconfig WHERE user_id = $1", member.id)
        if target_df_details is not None and target_df_details.get('dumbfight_rig_duration') is not None and target_df_details.get('dumbfight_rig_duration') > round(time.time()):
            target_has_shield_potion = target_df_details.get('dumbfight_result')
        else:
            target_has_shield_potion = None
        extra_info = None
        if author_has_shield_potion is not None:
            if target_has_shield_potion is not None:
                if author_has_shield_potion == target_has_shield_potion:
                    doesauthorwin = random.choice([True, False])
                    extra_info = get_statement(responses[4]).format(str(ctx.author), str(member))
                else:
                    if target_has_shield_potion is True:
                        extra_info = get_statement(responses[6]).format(ctx.author)
                        doesauthorwin = False
                    elif author_has_shield_potion is False:
                        extra_info = get_statement(responses[5]).format(ctx.author)
                        doesauthorwin = False
                    elif target_has_shield_potion is False:
                        extra_info = get_statement(responses[5]).format(member)
                        doesauthorwin = True
                    elif author_has_shield_potion is True:
                        extra_info = get_statement(responses[6]).format(ctx.author)
                        doesauthorwin = True
            else:
                if author_has_shield_potion is True:
                    extra_info = get_statement(responses[6]).format(ctx.author)
                    doesauthorwin = True
                else:
                    extra_info = get_statement(responses[5]).format(ctx.author)
                    doesauthorwin = False
        else:
            if target_has_shield_potion is not None:
                if target_has_shield_potion is True:
                    extra_info = get_statement(responses[6]).format(member)
                    doesauthorwin = False
                else:
                    extra_info = get_statement(responses[5]).format(member)
                    doesauthorwin = True
        channel = ctx.channel
        if isinstance(channel, discord.Thread):
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond("Dumbfight is not supported in threads yet. Sorry >.<", ephemeral=True)
        if doesauthorwin:
            muted = member
            color = 0x00ff00
            winner = ctx.author
        else:
            muted = ctx.author
            winner = member
            color = 0xff0000
        action = get_statement(random.choice(self.dumbfight_statements)).format(winner.mention, muted.mention)
        if extra_info is None:
            await self.client.db.execute("INSERT INTO dumbfightlog values($1, $2, $3)", ctx.author.id, member.id, 1 if doesauthorwin is True else 0)
        originaloverwrite = channel.overwrites_for(muted) if muted in channel.overwrites else None
        tempoverwrite = channel.overwrites_for(muted) if muted in channel.overwrites else discord.PermissionOverwrite()
        tempoverwrite.send_messages = False
        await channel.set_permissions(muted, overwrite=tempoverwrite)
        if ctx.channel.id in self.mutedusers:
            self.mutedusers[ctx.channel.id] = self.mutedusers[ctx.channel.id] + [muted.id]
        else:
            self.mutedusers[ctx.channel.id] = [muted.id]
        if ctx.author == member:
            um = get_statement(random.choice(responses[7:12])).format(ctx.author.mention)
            um += '\n' + random.choice(responses[13]).format(ctx.author, duration)
            embed = discord.Embed(title=get_statement(responses[12]), description=um, colour=color)
        else:
            desc = action + "\n" + get_statement(responses[14]).format(muted.mention, duration)
            embed = discord.Embed(title=get_statement(responses[12]), description=desc, colour=color)
        if extra_info is not None:
            embed.set_footer(text=extra_info, icon_url="https://cdn.discordapp.com/emojis/944226900988026890.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed, ephemeral=False)
        await asyncio.sleep(duration)
        await channel.set_permissions(muted, overwrite=originaloverwrite)
        if muted.id in self.mutedusers[ctx.channel.id]:
            if len(self.mutedusers[ctx.channel.id]) == 1:
                del self.mutedusers[ctx.channel.id]
            else:
                lst = self.mutedusers[ctx.channel.id]
                lst.remove(muted.id)
                self.mutedusers[ctx.channel.id] = lst