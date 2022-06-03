import asyncio
import contextlib
import json
import os

from main import dvvt
import discord
from discord.ext import commands, tasks
from time import time
from datetime import datetime
import pytz

dankmemerplayerrole_id = 982153033523793950 if os.getenv('state') == '1' else 837594909917708298

class GetDankMemerPlayerRole(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Get the Dank Memer Player role", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        if (role := interaction.guild.get_role(dankmemerplayerrole_id)) is not None:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"<:DVB_True:887589686808309791> Added **{role.name}**!\nNow head to a Dank Memer Bot channel to use the bot.", view=ChannelOnlyView(), ephemeral=True)


class GoToChannel(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Teleport to a Dank Memer Bot Channel", style=discord.ButtonStyle.grey, url="https://discord.com/channels/595457764935991326/614945340617130004")

class RoleOnlyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GetDankMemerPlayerRole())

class RoleAndChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GetDankMemerPlayerRole())
        self.add_item(GoToChannel())

class ChannelOnlyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GoToChannel())


class on_message(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
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
        if not message.author.bot:
            con = message.content.lower()
            if con.startswith('pls '):
                split_cmd = con.split(' ')
                if len(split_cmd) > 0:
                    if split_cmd[1] == 'rob':
                        return await message.channel.send(f"**Robbing is disabled** in {message.guild.name}. This is for the safety of everyone's wallets in this server.")
                    else:
                        if message.channel.id in [698462922682138654, 608498967474601995, 871737314831908974]:
                            if not message.channel.permissions_for(message.author).manage_messages:
                                if discord.utils.get(message.author.roles, id=dankmemerplayerrole_id):
                                    msg = f"{message.author.mention}\n**Dank Memer does __not__ work in this channel.**\n<:dv_peepoblush2OwO:837653921949548605> Dank Memer can be used in our channels meant for Dank Memer. You can also trade items with other users!<:dv_peepoBlushOwO:837653418017161236>\n\nClick the button below to head to one such channel!"
                                    await message.channel.send(msg, view=ChannelOnlyView())
                                else:
                                    msg = f"{message.author.mention}\n**Dank Memer does __not__ work in this channel.**\n<:dv_peepoblush2OwO:837653921949548605> Dank Memer can be used in our channels meant for Dank Memer. You can also trade items with other users!<:dv_peepoBlushOwO:837653418017161236>\n\nClick the button below to get the **Dank Memer Player** role and access these channels!"
                                    await message.channel.send(msg, view=RoleOnlyView())
                            else:
                                pass






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