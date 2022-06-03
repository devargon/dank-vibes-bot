import asyncio
import contextlib
import json
from main import dvvt
import discord
from discord.ext import commands, tasks
from time import time
from datetime import datetime
import pytz


class on_message(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 235148962103951360:
            if message.content.startswith('Exported') and len(message.attachments) > 0:
                await message.add_reaction("🧐")
                def check(payload):
                    return payload.message_id == message.id and str(payload.emoji) == "🧐" and payload.user_id != self.client.user.id
                try:
                    await self.client.wait_for("raw_reaction_add", check=check, timeout=60)
                except asyncio.TimeoutError:
                    return await message.remove_reaction("🧐", self.client.user)
                statusmsg = await message.reply("<a:DVB_typing:955345484648710154> **Reading exported modlog**...")
                attachment = message.attachments[0]
                data_bytes = await attachment.read()
                data = data_bytes.decode('utf-8')
                try:
                    data_json = json.loads(data)
                except json.decoder.JSONDecodeError:
                    return await statusmsg.edit(content="<:DVB_redcross:955345440356859944> **Error:** `JSONDecodeError`")
                else:
                    um = ""
                    emojis = {
                        'ban': '<:DVB_ban:930310804203503626>',
                        'mute': '<:DVB_Mute:930308084885241926>',
                        'kick': '👢',
                        'unmute': '<:DVB_Unmute:930308214132707338>',
                        'unban': '<:DVB_Unban:930308373440765982>',
                        'warn': '<:DVB_warn:930312114629931028>',
                        'tempban': '<:DVB_tempban:930310741213454336>'
                    }
                    for modcase in data_json:
                        moderator_id = modcase.get('moderator_id')
                        moderator = self.client.get_user(moderator_id) or moderator_id
                        action = modcase.get('action')
                        reason = modcase.get('reason')
                        timestamp = modcase.get('timestamp')
                        timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.utc).timestamp()
                        timestamp = f"<t:{round(timestamp)}>"
                        symbol = emojis.get(action) if action in emojis else action
                        if reason is None:
                            tempstr = f"{symbol} by **{moderator}** on {timestamp}"
                        else:
                            tempstr = f"{symbol} by **{moderator}** on {timestamp}: {reason}"
                        if len(symbol) + len(tempstr) + len(um) < 1990:
                            um += f"{tempstr}\n"
                        else:
                            await message.channel.send(um)
                            um = f"{tempstr}\n"
                    await message.channel.send(um)
                    await message.channel.send("What it means:\n<:DVB_ban:930310804203503626> - Ban\n<:DVB_Mute:930308084885241926> - Mute\n<:DVB_Unmute:930308214132707338> - Unmute\n<:DVB_Unban:930308373440765982> - Unban\n<:DVB_warn:930312114629931028> - Warn\n<:DVB_tempban:930310741213454336> - Tempban")


    @commands.Cog.listener()
    async def on_member_update(self, member_before, member_after):
        if member_before.display_name != member_after.display_name:
            old_nickname = member_before.display_name
            new_nickname = member_after.display_name
            if f"[AFK] {old_nickname}" == new_nickname:
                return
            if f"[AFK] {new_nickname}" == old_nickname:
                return
            result = await self.client.db.fetchrow(
                "SELECT * FROM freezenick WHERE user_id = $1 and guild_id = $2", member_after.id,
                member_after.guild.id)
            if result is not None:
                if result.get('nickname') == new_nickname:
                    return
                if result.get('nickname') == old_nickname:
                    return
                if result.get('old_nickname') == new_nickname:
                    return
                if result.get('old_nickname') == old_nickname:
                    return
            await self.client.db.execute("INSERT INTO nickname_changes VALUES($1, $2, $3, $4)",
                                              member_before.guild.id, member_before.id, new_nickname, round(time()))

    def cog_unload(self) -> None:
        pass