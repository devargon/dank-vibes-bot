import discord

from utils.context import DVVTcontext
from utils.helper import paste
from typing import Union, Literal, Optional
from utils.format import human_join


def make_embed(user, target, action, details=None):
    if details is None:
        details = {}
    if target is None:
        description = f"Executed by **{user.mention}**"
    else:
        if type(target) == str:
            target_disp = target
        else:
            target_disp = target.mention
        description = f"Executed by **{user.mention}** for {target_disp}"
    embed = discord.Embed(
        title=action,
        description=description,
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.display_avatar.url)
    embed.set_footer(text=str(user.id))
    for i, v in details.items():
        embed.add_field(name=i, value=v if v is not None and len(v) > 0 else "\u200b", inline=False)
    return embed


class BotLogger:
    def __init__(self, client):
        self.client = client

    async def send_log(self, guild_or_context: Union[DVVTcontext, discord.Guild], embed: discord.Embed, text: str = None):
        if isinstance(guild_or_context, DVVTcontext):
            guild = guild_or_context.guild
        else:
            guild = guild_or_context
        config = await self.client.get_guild_settings(guild.id)
        log_channel_id = config.log_channel
        if (channel := self.client.get_channel(log_channel_id)) is not None:
            webhook = await self.client.get_webhook(channel)
            if webhook is not None:
                await webhook.send(content=text, embed=embed)

    async def log_sticky_action(self, action: Literal['add', 'remove'], user, channel, message = None):
        action = action.lower()
        if action not in ['add', 'remove']:
            return
        if action == "add":
            title = "Add Sticky Message"
        else:
            title = "Remove Sticky Message"

        if message is not None:
            link = await paste(message)
            details = {"message": link}
        else:
            details = {}
        embed = make_embed(user, channel, title, details)
        await self.send_log(channel.guild, embed=embed)

    async def log_messagecommand(self, action: Literal['add', 'remove'], user, bot, channels):
        action = action.lower()
        if action not in ['add', 'remove']:
            return
        if action == "add":
            title = "Add bot/channels to MessageCleanup"
        else:
            title = "Remove bot/channel(s) from MessageCleanup"
        if type(bot) != list:
            bot = [bot]
        bots_proper = [f"{_bot.name}#{_bot.discriminator}" for _bot in bot]
        human_bots = human_join(bots_proper, final="and") if len(bots_proper) is not None else "None"
        if type(channels) != list:
            channels = [channels]
        channels_proper = [f"{_channel.mention}" for _channel in channels]
        human_channels = human_join(channels_proper, final="and") if len(channels_proper) is not None else "None"
        details = {"Bots affected": human_bots, "Channels affected": human_channels}
        embed = make_embed(user, None, title, details)
        await self.send_log(user.guild, embed=embed)

    async def log_messagecommand_message(self, user, target, message):
        link = await paste(message)
        details = {"Message": link}
        embed = make_embed(user, target, "MessageCleanup Set Message", details)
        await self.send_log(target.guild, embed=embed)

    async def log_lockdown(self, action: Literal['start', 'end'], user, lockdown_profile):
        action = action.lower()
        if action not in ['start', 'end']:
            return
        if action == 'start':
            title = "Start Lockdown"
        else:
            title = "End Lockdown"
        embed = make_embed(user, f"the profile **{lockdown_profile}**", title)
        await self.send_log(user.guild, embed=embed)

    async def log_lockdown_message(self, user, before_text, after_text, lockdown_profile, is_start_message):
        before_text_link = await paste(before_text)
        after_text_link = await paste(after_text)
        details = {
            "Before": before_text_link,
            "After": after_text_link,
            "For": is_start_message
        }
        embed = make_embed(user, lockdown_profile, "Set Lockdown Message", details)
        await self.send_log(user.guild, embed=embed)

    async def log_approved_nickname(self, user, target, nickname: str):
        details = {"New Nickname": nickname}
        embed = make_embed(user, target, "Approve Nickname", details)
        await self.send_log(user.guild, embed=embed)

    async def log_donation_edit(self, action: Literal['add', 'remove', 'set'], user, target, amount):
        action = action.lower()
        if action not in ['add', 'remove', 'set']:
            return
        details = {
            "User ID of target": str(target.id),
            "Amount": amount
        }
        if action == 'add':
            title = "Add Donation"
        elif action == 'remove':
            title = "Remove Donation"
        else:
            title = "Set Donation"
        embed = make_embed(user, target, title, details)
        await self.send_log(user.guild, embed=embed)




