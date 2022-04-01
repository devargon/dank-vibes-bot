import discord
from discord.ext import commands

from utils.context import DVVTcontext
from utils.format import get_command_name
from time import time

class Verify(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label='Verify your account via discord.com',
                                        url="https://discord.com/api/oauth2/authorize?client_id=866346404573216769&redirect_uri=https%3A%2F%2Fverify.dvbot.nogra.me&response_type=code&scope=identify",
                                        emoji=discord.PartialEmoji.from_str('<a:c_redcheck:915527725807185971>')))


class Logging(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: DVVTcontext):
        if ctx.author.id not in self.client.reminded_about_verification and time() < 1648893600:
            if await self.client.pool_pg.fetchval("SELECT verification_reminded FROM userconfig WHERE user_id = $1", ctx.author.id) is not True:
                msg = f"Suspicious activity from you has been detected by {self.client.user.name}'s automod function. From **April 2 00:00 Pacific Time**, you will **not** be able to use {self.client.user.name} and its commands.\nTo remove this ban, verify your account at <https://discord.com/api/oauth2/authorize?client_id=866346404573216769&redirect_uri=https%3A%2F%2Fverify.dvbot.nogra.me&response_type=code&scope=identify>, so that your activity can be validated and you can use the bot as per normal.\n\n**This message will be sent only once.**"
                await self.client.pool_pg.execute("INSERT INTO userconfig (user_id, verification_reminded) VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET verification_reminded = $2", ctx.author.id, True)
                self.client.reminded_about_verification.append(ctx.author.id)
                try:
                    await ctx.reply(msg, view=Verify())
                except discord.Forbidden:
                    await ctx.send(f"{ctx.author.mention} " + msg, view=Verify())
            else:
                self.client.reminded_about_verification.append(ctx.author.id)
        command_name = get_command_name(ctx.command)
        user_id = ctx.author.id
        timeofexecution = round(time())
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id
        message = ctx.message.content
        message_id = ctx.message.id
        await self.client.pool_pg.execute("INSERT INTO commandlog(guild_id, channel_id, user_id, command, message, time, message_id, is_application_command) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)", guild_id, channel_id, user_id, command_name, message, timeofexecution, message_id, False)

    @commands.Cog.listener()
    async def on_application_command_completion(self, ctx: discord.ApplicationContext):
        command_name = ctx.command.qualified_name
        user_id = ctx.author.id
        timeofexecution = round(time())
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id
        await self.client.pool_pg.execute(
            "INSERT INTO commandlog(guild_id, channel_id, user_id, command, message, time, is_application_command) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            guild_id, channel_id, user_id, command_name, "", timeofexecution, True
        )


    @commands.Cog.listener()
    async def on_message(self, message):
        if self.client.maintenance.get(self.qualified_name):
            return
        if not isinstance(message.channel, discord.DMChannel):
            return
        if message.author == self.client.user:
            return
        if message.author.id in [642318626044772362, 727409176946409543, 663867896195186698]:
            return
        embed = discord.Embed(title=f"Message sent to {self.client.user.name} via DMs", description=message.content or "No content", color=0x09ffe0, timestamp=discord.utils.utcnow())
        if len(message.attachments) > 0:
            attachments = []
            for attachment in message.attachments:
                if attachment.content_type in ["image/apng", "image/gif", "image/jpeg", "image/png", "image/webp"]:
                    if not embed.image:
                        embed.set_image(url=attachment.proxy_url)
                    else:
                        attachments.append(attachment.proxy_url)
                else:
                    attachments.append(attachment.proxy_url)
            if len(attachments) > 0:
                embed.add_field(name="Attachments", value="\n".join(attachments), inline=False)
        embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url)
        log_channel = self.client.get_channel(889111152561369158)
        webhooks = await log_channel.webhooks()
        webhook = discord.utils.get(webhooks, name=self.client.user.name)
        if webhook is None:
            try:
                webhook = await log_channel.create_webhook(name=self.client.user.name)
            except discord.Forbidden:
                try:
                    await log_channel.send("I am unable to create a webhook to send a log.")
                except (discord.HTTPException, discord.Forbidden):
                    return
                return
        await webhook.send(embed=embed, username=self.client.user.name, avatar_url=self.client.user.display_avatar.url)
