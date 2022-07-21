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

modcommands_id = 978563862896967681 if os.getenv('state') == '1' else 616007729718231161
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


class OnMessage(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

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
            settings = await self.client.get_guild_settings(message.guild.id)
            con = message.content.lower()
            if settings.pls_ar is True:
                if con.startswith('pls '):
                    split_cmd = con.split(' ')
                    if len(split_cmd) > 1:
                        if split_cmd[1] == 'rob':
                            return await message.channel.send(f"**Robbing is disabled** in {message.guild.name}. This is for the safety of everyone's wallets in this server.")
                        else:
                            whitelisted_user_ids = [758173667682287616, 758175713983201300]
                            if message.channel.id in [698462922682138654, 608498967474601995, 871737314831908974] and not any(discord.utils.get(message.author.roles, id=roleid) for roleid in whitelisted_user_ids):
                                if not message.channel.permissions_for(message.author).manage_messages:
                                    if discord.utils.get(message.author.roles, id=dankmemerplayerrole_id):
                                        msg = f"{message.author.mention}\n**Dank Memer does __not__ work in this channel.**\nClick below to head to a Bot channel to use Dank Memer."
                                        await message.channel.send(msg, view=ChannelOnlyView())
                                    else:
                                        msg = f"{message.author.mention}\n**Dank Memer does __not__ work in this channel.**\n<:dv_peepoblush2OwO:837653921949548605> The Dank Memer bot can be used in channels just for Dank Memer. <:dv_peepoBlushOwO:837653418017161236>\n\nClick the button below to get the **Dank Memer Player** role and access these channels!"
                                        await message.channel.send(msg, view=RoleOnlyView())
                                else:
                                    pass
            if settings.mrob_ar is True:
                if con.startswith('m.rob') or con.startswith('m.steal'):
                    split_cmd = con.split(' ')
                    if len(split_cmd) > 1:
                        embed = discord.Embed(title="A MafiaBot rob attempt was made by this user.", description=f"```\n{message.content}\n```\n[Jump to message]({message.jump_url}) in {message.channel.mention}", color=discord.Color.red())
                        embed.add_field(name="If this was a valid rob attempt...", value="Run the command shown above.")
                        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/543971450068008961.png?v=1")
                        embed.set_author(icon_url=message.author.display_avatar.with_size(32).url, name=f"{message.author} ({message.author.id})")
                        modc = self.client.get_channel(modcommands_id)
                        await modc.send(f"```\n-temprole {message.author.id} 6h No Minigames\n```", embed=embed)
                        offender_msg = f"{message.author.mention}\n⛔ **Robbing in any bot is prohibited in {message.guild.name}**.\nA report regarding your actions has been sent to the moderators."
                    else:
                        offender_msg = f"{message.author.mention}\n⛔ **Robbing in any bot is prohibited in {message.guild.name}**.\nIf you try to rob a user in MafiaBot, a report will be sent and action will be taken."
                    try:
                        await message.reply(offender_msg)
                    except Exception as e:
                        await message.channel.send(offender_msg)
        if message.channel.id in self.client.mafia_channels.keys():
            #mafia logging
            log_channel_id = self.client.mafia_channels[message.channel.id]
            log_channel = message.guild.get_channel(log_channel_id)
            if log_channel is not None:
                webh = await self.client.get_webhook(log_channel)
                original_content = message.content
                add_author_label = f"`{message.author} - {message.author.id}`"
                if len(add_author_label+"\n"+original_content) > 2000:
                    embed = discord.Embed(description=add_author_label, color=self.client.embed_color)
                    content_formatted = original_content
                else:
                    embed = None
                    content_formatted = add_author_label+"\n"+original_content
                embeds = message.embeds
                if embed is not None:
                    embeds.append(embed)
                await webh.send(
                    content=content_formatted,
                    username=message.author.display_name,
                    avatar_url=message.author.display_avatar.with_size(128).url,
                    embeds=embeds,
                    allowed_mentions=discord.AllowedMentions.none()
                )










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