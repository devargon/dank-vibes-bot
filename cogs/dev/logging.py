import discord
from discord.ext import commands
from utils.format import get_command_name, proper_userf
from time import time

class ReplyModal(discord.ui.Modal):
    def __init__(self, user, interaction_message, user_message):
        self.user = user
        self.interaction_message: discord.Message = interaction_message
        self.user_message: discord.Message = user_message
        self.response = None
        super().__init__(title=f"Reply to {user.name}")
        self.add_item(discord.ui.InputText(label="Message", style=discord.InputTextStyle.long, min_length=1, max_length=2000, placeholder="Among Us??!?", required=True))

    async def callback(self, interaction: discord.Interaction):
        response = self.children[0].value
        formatted_content = self.user_message.content if len(self.user_message.content) < 1900 else self.user_message.content[:1900] + "..."
        embed = discord.Embed(title=f"{self.user} sent:", description=f"{self.user_message.content}", color=interaction.client.embed_color)
        embed.add_field(name="You replied", value=response)
        if (enabled := await interaction.client.db.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", interaction.user.id)) is not True:
            return await interaction.response.send_message("**HTTP 403 Forbidden**\nReplying to the message failed.", embed=embed, ephemeral=True)
        else:
            try:
                await self.user_message.reply(content=response)
            except Exception as e:
                result_embed = discord.Embed(title=f"Failed to reply to {proper_userf(self.user)}'s message", description=f"```py\n{e}\n```", color=discord.Color.red())
            else:
                result_embed = discord.Embed(title="Success!", description=f"Message was sent to {self.user}.", color=discord.Color.green())
            await interaction.response.send_message(embeds=[embed, result_embed], ephemeral=True)





class ReplyToMessage(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Reply to Message", custom_id="DMReplyToMessage")
    async def reply_to_message(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        user_id = embed.author.name.split(' ')[-1]
        user_id = user_id.replace('(', '').replace(')', '')
        user_id = int(user_id)
        message_id = int(embed.footer.text)
        user = await interaction.client.fetch_user(user_id)
        if user is not None:
            try:
                m = await user.fetch_message(message_id)
            except Exception as e:
                result_embed = discord.Embed(title=f"Failed to fetch message", description=f"```py\n{e}\n```", color=discord.Color.red())
                return await interaction.response.send_message(embed=result_embed, ephemeral=True)
            else:
                await interaction.response.send_modal(ReplyModal(user, interaction.message, m))
        else:
            result_embed = discord.Embed(title=f"User wasn't found.", color=discord.Color.red())
            return await interaction.response.send_message(embed=result_embed, ephemeral=True)




class Logging(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        command_name = get_command_name(ctx.command)
        user_id = ctx.author.id
        timeofexecution = round(time())
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id
        message = ctx.message.content
        message_id = ctx.message.id
        await self.client.db.execute("INSERT INTO commandlog(guild_id, channel_id, user_id, command, message, time, message_id, is_application_command) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)", guild_id, channel_id, user_id, command_name, message, timeofexecution, message_id, False)

    @commands.Cog.listener()
    async def on_application_command_completion(self, ctx: discord.ApplicationContext):
        command_name = ctx.command.qualified_name
        user_id = ctx.author.id
        timeofexecution = round(time())
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id
        await self.client.db.execute(
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
        embed = discord.Embed(title=f"Message sent to DMs", description=message.content or "No content", color=0x09ffe0, timestamp=discord.utils.utcnow())
        embed.set_footer(text=str(message.id))
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
        webhook = await self.client.get_webhook(log_channel)
        await webhook.send(embed=embed, username=self.client.user.name, avatar_url=self.client.user.display_avatar.url, view=ReplyToMessage())
