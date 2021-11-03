import discord
from utils import checks
from discord.ext import commands
from datetime import datetime
import aiohttp

status_emojis = {
    discord.Status.dnd: "<:status_dnd:840918521918783508>",
    discord.Status.idle: "<:status_idle:840918469327192096>",
    discord.Status.online: "<:status_online:840918419246415873>",
    discord.Status.offline: "<:status_offline:840918448560930867>",
    discord.Status.invisible: "<:status_offline:840918448560930867>",
    discord.Status.do_not_disturb: "<:status_dnd:840918521918783508>",
}

class Logging(commands.Cog):
    def __init__(self, client):
        self.client = client

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
                if attachment.content_type in["image/apng", "image/gif", "image/jpeg", "image/png", "image/webp"]:
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
        webhook = discord.utils.get(webhooks, name = self.client.user.name)
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