import asyncio
import contextlib
import json
import operator
import os
import asyncio
import re
import textwrap

import typing

import aiohttp

from utils.format import human_join, durationdisplay, proper_userf, print_exception

from main import dvvt
import discord
from discord.ext import commands, tasks
from time import time
from datetime import datetime
import pytz
from utils.context import DVVTcontext

modcommands_id = 978563862896967681 if os.getenv('state') == '1' else 616007729718231161
dankmemerplayerrole_id = 982153033523793950 if os.getenv('state') == '1' else 837594909917708298

ID_REGEX = re.compile(r"([0-9]{15,20})")

class DeleteChannel(discord.ui.View):
    def __init__(self):
        self.delete = False
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete this channel", emoji="🗑", style=discord.ButtonStyle.red)
    async def delete_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if "mafia-at" not in interaction.channel.name:
            await interaction.response.send_message("This button cannot be used here.")
        else:
            if self.delete is True:
                self.delete = False
                await interaction.response.send_message("Cancelled channel deletion.")
            else:
                self.delete = True
                await interaction.response.send_message("This channel will be deleted in 10 seconds, press the button again to cancel.")
                await asyncio.sleep(10)
                if self.delete is True:
                    await interaction.channel.delete()


class MafiaGameDetails:
    def __init__(self, players: typing.List[discord.Member]):
        self.players = players
        self.message_count = {}
        self.deaths = {}
        for i in self.players:
            self.message_count[i.id] = 0
        self.night = 1

    def add_message_count(self, member: discord.Member):
        if member.id in self.message_count:
            self.message_count[member.id] += 1


def get_dead_users(embed: discord.Embed, embed_type: typing.Literal['day', 'night']):
    dead = []
    if embed_type == 'day':
        dead_field = embed.fields[1]
        value = dead_field.value
        if type(value) == str and len(value) > 0: ## in case somehow the content is empty
            for line in value.split('\n'):
                try:
                    user_id = ID_REGEX.findall(line)[0]
                    user_id = int(user_id)
                except Exception as e:
                    pass
                else:
                    dead.append(user_id)
    elif embed_type == 'night':
        description = embed.description
        if type(description) == str and len(description) > 0: ## in case somehow the content is empty
            for line in description.split('\n'):
                try:
                    user_id = ID_REGEX.findall(line)[0]
                    user_id = int(user_id)
                except Exception as e:
                    pass
                else:
                    dead.append(user_id)
    return dead


def get_channel_name(channel: discord.abc.GuildChannel):
    time_created_at = channel.created_at.strftime("%H-%M-%S-utc")
    log_channel_name = f"mafia-at-{time_created_at}"
    return log_channel_name

def return_emoji(truefalse: bool):
    if truefalse:
        return "<:DVB_True:887589686808309791> "
    else:
        return "<:DVB_False:887589731515392000>"

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
        self.mafia_wait = False
        self.pls_prompt = {}
        self.k_prompt = {}
        self.active_eboy_message_ids = []


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            if message.guild is None and message.author.id == self.client.user.id and isinstance(message.channel, discord.DMChannel) and message.webhook_id is None:
                try:
                    log_c = self.client.get_channel(int(os.getenv("BOT_DM_LOG_CHANNEL") or ""))
                except ValueError:
                    log_c = None
                if log_c is not None:
                    w = await self.client.get_webhook(log_c)
                    c = message.content or ""
                    # if message.jump_url is not None
                    recipient = None
                    if message.channel.jump_url is not None:
                        try:
                            dm_c_id = message.channel.jump_url.split("/")[-1]
                        except IndexError:
                            pass
                        else:
                            try:
                                dm_c: discord.DMChannel = self.client.get_channel(int(dm_c_id))
                            except ValueError:
                                pass
                            else:
                                recipient = dm_c.recipient
                    if recipient is not None:
                        for_ = f"For {recipient.name} {recipient.id}"
                    else:
                        for_ = f"DM CID: {message.channel.id}"
                    c = textwrap.shorten(f"*{for_} DM MID {message.id}*\n\n{c}", 2000)
                    e = message.embeds or []
                    v = discord.ui.View.from_message(message) if len(message.components) > 0 else None
                    if v is not None:
                        await w.send(content=c, embeds=e, view=v)
                    else:
                        await w.send(content=c, embeds=e)
        except Exception as e:
            print_exception("Error while logging bot-initiated DMs:", e)
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
                    await message.remove_reaction("🧐", self.client.user)
                else:
                    statusmsg = await message.reply("<a:DVB_typing:955345484648710154> **Reading exported modlog**...")
                    attachment = message.attachments[0]
                    data_bytes = await attachment.read()
                    data = data_bytes.decode('utf-8')
                    try:
                        data_json = json.loads(data)
                    except json.decoder.JSONDecodeError:
                        await statusmsg.edit(content="<:DVB_redcross:955345440356859944> **Error:** `JSONDecodeError`")
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
            settings = await self.client.get_guild_settings(message.guild.id)
            if settings.pls_ar is True:
                if con.startswith('pls '):
                    split_cmd = con.split(' ')
                    if len(split_cmd) > 1:
                        if split_cmd[1] == 'rob':
                            await message.channel.send(f"**Robbing is disabled** in {message.guild.name}. This is for the safety of everyone's wallets in this server.")
                        else:
                            last_sent = self.pls_prompt.get(message.channel.id, 0)
                            if round(time()) - last_sent >= 120:
                                if message.channel.category_id in [644006682392788992, 797167555767697408, 947298067500114061, 608505446717849630, 802467427208265728, 763457841133912074, 789195494664306688, 783299769580781588, 805052824185733120, 834696686923284510, 847897065081274409, 875316745416617984]:
                                    embed = discord.Embed(title="Dank Memer has switched to slash commands.", description="**`pls` commands have been replaced** with <:DVB_commands:913426937869926440> **slash commands.**\nType `/` to find your favorite Dank Memer command.\n\n`pls help` → `/help`\n`pls beg` -> `/beg`\n\nIf you have answers or queries, join [Dank Memer's Support Server.](https://discord.gg/dankmemerbot)", color=0xff0000)
                                    embed.set_footer(text=message.guild.name, icon_url=message.guild.icon.url)
                                    embed.set_image(url="https://cdn.nogra.xyz/dankvibes/slashbanner.png")
                                    if not message.channel.permissions_for(message.author).manage_messages:
                                        await message.channel.send(content=message.author.mention, embed=embed)
                                        self.pls_prompt[message.channel.id] = round(time())
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
        if message.interaction is not None and message.interaction.name == "setup" and self.mafia_wait is not True:
            lounge_category = 595457764935991327 if message.guild.id == 595457764935991326 else 875316745416617984
            if message.channel.id == 711377990113820924 or discord.utils.get(message.author.roles, id=735417263968223234) or discord.utils.get(message.author.roles, id=724971657143255170) or message.author.guild_permissions.manage_roles:
                #         it will treat it as a to be monitored game if it's in events, or user is a modm+/event hoster or event sponsor
                status = ["<a:DVB_CLoad3:994913503771111515> Waiting for Mafia Channel creation."]
                self.mafia_wait = True
                mafia_status_msg = await message.channel.send("\n".join(status))
                async def safe_edit(m):
                    try:
                        await m.edit(content="\n".join(status))
                        return m
                    except:
                        return await message.channel.send("\n".join(status))
                def check(channel: discord.abc.GuildChannel):
                    return channel.name == 'mafia' and channel.category_id == lounge_category
                try:
                    mafia_channel = await self.client.wait_for('guild_channel_create', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    status = [f"{return_emoji(False)} **I could not detect a mafia channel created** in the last minute. Try to start it manually with `dv.afkmafia` instead."]
                    mafia_status_msg = await safe_edit(mafia_status_msg)
                    self.mafia_wait = False
                else:
                    status = [f"{return_emoji(True)} {mafia_channel.mention} game found", "<a:DVB_CLoad2:994913353388527668> Setting up Mafia Log channel..."]
                log_channel_name = get_channel_name(mafia_channel)
                if message.guild.id == 595457764935991326:
                    # set perms if the game was started in mafia
                    event_hoster_role = message.guild.get_role(735417263968223234)
                    event_manager_role = message.guild.get_role(756667326623121568)
                    planet_role = message.guild.get_role(649499248320184320)
                    mod_manager_role = message.guild.get_role(684591962094829569)
                    overwrites = {}
                    manager_overwrite = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        add_reactions=True,
                        embed_links=True,
                        read_message_history=True,
                        use_external_emojis=True,
                        attach_files=True,
                        use_external_stickers=True,
                        manage_messages=False
                    )
                    overwrites[message.guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                    if planet_role is not None:
                        overwrites[planet_role] = discord.PermissionOverwrite(view_channel=False)
                    if event_hoster_role is not None:
                        overwrites[event_hoster_role] = manager_overwrite
                    if event_manager_role is not None:
                        overwrites[event_manager_role] = manager_overwrite
                    if mod_manager_role is not None:
                        overwrites[mod_manager_role] = manager_overwrite
                    log_channel = await message.guild.create_text_channel(name=log_channel_name, category=message.guild.get_channel(lounge_category), overwrites=overwrites, reason="Mafia Game tracking", topic=f"For the {mafia_channel.mention} game that was started at <t:{round(mafia_channel.created_at.timestamp())}>.")
                else:
                    log_channel = await message.guild.create_text_channel(name=log_channel_name, category=message.guild.get_channel(lounge_category), reason="Mafia Game tracking", topic=f"For the {mafia_channel.mention} game that was started at <t:{round(mafia_channel.created_at.timestamp())}>.")

                webhook = await log_channel.create_webhook(name=self.client.user.name)
                self.client.webhooks[log_channel.id] = webhook
                self.client.mafia_channels[mafia_channel.id] = log_channel.id
                status[1] = f"{return_emoji(True)} {log_channel.mention} Mafia Log channel created."
                mafia_status_msg = await safe_edit(mafia_status_msg)
                self.mafia_wait = False
                await message.channel.send(f"**The Mafia logging channel {log_channel.mention} has been created**, it is now safe to start the game.")
        if message.channel.id in self.client.mafia_channels.keys():
            #mafia logging
            log_channel_id = self.client.mafia_channels[message.channel.id]
            log_channel = message.guild.get_channel(log_channel_id)
            if log_channel is not None:
                if len(message.mentions) > 0 and message.author.id == 511786918783090688:
                    if message.channel.id not in self.client.mafia_game_details:
                        rules = """<a:dv_wExclamationOwO:837787071531450368> **__Remember:__** <a:dv_wExclamationOwO:837787071531450368> 
<:d_snowydash:921327788223500288> You must be __actively__ participating in order to receive a prize. Merely interacting in MafiaBot's DMs does not count.
<:d_snowydash:921327788223500288> You are not allowed to send __screenshots__ or __copy/paste__ messages from the bot.
<:d_snowydash:921327788223500288> You are not allowed to __reveal information__ after you are __dead__.
<:d_snowydash:921327788223500288>  Visiting the sponsor on the first night is not allowed.
<:d_snowydash:921327788223500288> Random shooting n1 as Vigilante is not allowed (Falls under gamethrowing)
<:d_snowydash:921327788223500288> __Illegal teaming__ is not allowed (ex: executioner teaming with their target).
<:d_snowydash:921327788223500288> __Bribing__ other players is not allowed."""
                        self.client.mafia_game_details[message.channel.id] = MafiaGameDetails(message.mentions)

                        if message.guild.id == 595457764935991326: # dank vibes event sposnor stuff
                            event_sponsor_role = message.guild.get_role(724971657143255170) # event sponsor role, check if event sponsor joined the event
                            if event_sponsor_role is not None:
                                sponsors_in_game = []
                                for a in event_sponsor_role.members:
                                    if a in message.mentions:
                                        sponsors_in_game.append(f"**{a}** {a.mention}")
                                if len(sponsors_in_game) > 0:
                                    rules = f"**NOTE**:\n{human_join(sponsors_in_game, final='and')} are sponsors of this game. **__Do not__** target them on the first night.\n\n" + rules
                        mentions = '\n'.join([b.mention for b in message.mentions])
                        rules = f"{mentions}\n\n" + rules
                        await message.channel.send(rules)
                game_details: MafiaGameDetails = self.client.mafia_game_details.get(message.channel.id, None)
                if game_details is not None:
                    if message.author.bot is True:
                        if message.author.id == 511786918783090688:
                            if len(message.embeds) > 0:
                                embed = message.embeds[0]

                                if isinstance(embed.title, str):
                                    if embed.title.startswith("Night ") and embed.title[-1].isdigit():  # Sent after day ended, so it represents a day
                                        game_details.night = int(embed.title[-1])
                                        dead_users = get_dead_users(embed, 'day')
                                        for user in dead_users:
                                            if user not in game_details.deaths.keys():
                                                game_details.deaths[user] = f"Died ☀ D**{game_details.night-1}**"

                                    elif embed.title.startswith("Currently ded:"):  # sent after night ended, so it represents a night, might not appear if there's no one dead
                                        dead_users = get_dead_users(embed, 'night')
                                        for user in dead_users:
                                            if user not in game_details.deaths.keys():
                                                game_details.deaths[user] = f"Died 🌘 N**{game_details.night}**"

                    else:
                        game_details.add_message_count(message.author)

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
        if message.channel.name == 'mafia':
            lounge_category = 595457764935991327 if message.guild.id == 595457764935991326 else 875316745416617984
            if message.channel.category_id == lounge_category:
                if message.channel.id not in self.client.mafia_channels.keys():
                    log_channel = discord.utils.get(message.guild.channels, name=get_channel_name(message.channel))
                    if log_channel is not None:
                        self.client.mafia_channels[message.channel.id] = log_channel.id
                        await message.channel.send("This channel's log has been restored after a bot restart.")
        if message.channel.category_id in [802467427208265728, 763457841133912074, 789195494664306688, 783299769580781588, 805052824185733120, 834696686923284510, 847897065081274409]: # private channels
            def qualify():
                if message.author.bot:
                    if message.interaction is not None:
                        return "interaction"
                    elif (
                        message.author.id == 270904126974590976 and
                        len(message.embeds[0]) > 0 and
                        message.embeds[0].footer is not None and
                        message.embeds[0].footer.text is not None and
                        type(message.embeds[0].footer.text) == str and
                        "flow" in message.embeds[0].footer.text
                    ):
                        return "flow"
                    else:
                        return None
                else:
                    return "direct"

            q = qualify()
            c = await self.client.db.fetchrow("SELECT * FROM channels WHERE channel_id = $1", message.channel.id)
            if c is not None:
                if q == "interaction":
                    owner = message.interaction.user
                elif q == "flow":
                    context = await self.client.get_context(message, cls=DVVTcontext)
                    str_split = message.embeds[0].footer.text.split(" is running a ")
                    username = str_split[0]
                    try:
                        member = await commands.MemberConverter().convert(context, username)
                    except Exception as e:
                        owner = None
                    else:
                        owner = member
                elif q == "direct":
                    owner = message.author
                else:
                    owner = None
                if owner is not None and c.get('owner_id') == owner.id:
                    now = round(time())
                    await self.client.db.execute("UPDATE channels SET last_used = $1 WHERE channel_id = $2", now, message.channel.id)

        # IMPORTANT: IF YOU'RE DEVELOPING ANY MORE MESSAGE EVENTS, THIS ONE MIGHT BLOCK FOR 5 MINUTES
        """
        IMPORTANT: IF YOU'RE DEVELOPING ANY MORE MESSAGE EVENTS, THIS ONE MIGHT BLOCK FOR 5 MINUTES
        """
        if message.guild is not None and isinstance(message.author, discord.Member) and (discord.utils.get(message.author.roles, id=758174046365679686) or message.channel.id == 871737314831908974) and (":3" in message.content or ";3" in message.content):
            await message.add_reaction("<a:DVB_peoplewhooverusethisisweird:1218423094331445259>")
            # self.active_eboy_message_ids.append(message.id)
            def check2(payload):
                return payload.message_id == message.id \
                    and str(payload.emoji) == "<a:DVB_peoplewhooverusethisisweird:1218423094331445259>" \
                    and not message.author.bot \
                    and payload.user_id not in [866346404573216769, 771916467523551243]
            try:
                rrae: discord.RawReactionActionEvent = await self.client.wait_for("raw_reaction_add", check=check2, timeout=300)
            except asyncio.TimeoutError:
                pass
            else:

                try:
                    await message.reply(file=discord.File(fp="assets/miscellaneous/eboy.png"), delete_after=120.0)
                except Exception as e:
                    print_exception("Error while handling :3 reaction", e)
            finally:
                try:
                    await message.clear_reaction("<a:DVB_peoplewhooverusethisisweird:1218423094331445259>")
                except (discord.HTTPException, discord.NotFound, discord.InvalidArgument):
                    pass
                except discord.Forbidden:
                    try:
                        await message.remove_reaction("<a:DVB_peoplewhooverusethisisweird:1218423094331445259>", self.client.user)
                    except:
                        pass












    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        print("Sanity check 1")
        if isinstance(channel, discord.TextChannel):
            await self.client.db.execute("UPDATE channels SET active = False WHERE channel_id = $1", channel.id)
            print("Sanity check 2")
            if channel.name == 'mafia':
                print("Sanity check 3")
                if channel.id in self.client.mafia_channels.keys():
                    print("Sanity check 4")
                    log_channel_id = self.client.mafia_channels[channel.id]
                    print("Sanity check 5")
                    mafia_log_channel = channel.guild.get_channel(log_channel_id)
                    print("Sanity check 6")
                    if mafia_log_channel is not None:
                        print("Sanity check 7")
                        webh = await self.client.get_webhook(mafia_log_channel)
                        print("Sanity check 8")
                        del self.client.mafia_channels[channel.id]
                        print("Sanity check 9")
                        message_count = []
                        print("Sanity check 10")
                        game_details: MafiaGameDetails = self.client.mafia_game_details.pop(channel.id, None)
                        print("Sanity check 11")
                        if game_details is not None:
                            print("Sanity check 12")
                            a = sorted(game_details.message_count.items(), key=operator.itemgetter(1), reverse=True)
                            print("Sanity check 13")
                            for user_id, m_count in a:
                                print("Sanity check 14")
                                user = self.client.get_user(user_id) or user_id
                                print("Sanity check 15")
                                user_death = game_details.deaths.get(user_id, "")
                                print("Sanity check 16")
                                user_death = f"({user_death})" if user_death != "" else ""
                                print("Sanity check 17")
                                message_count.append(f"**{proper_userf(user)}**: {m_count} messages {user_death}")
                                print("Sanity check 18")
                            message_count = "\n".join(message_count)
                            print("Sanity check 19")
                            duration = discord.utils.utcnow() - channel.created_at
                            print("Sanity check 20")
                            duration = duration.total_seconds()
                            print("Sanity check 21")
                            summary_embed = discord.Embed(title=f"{durationdisplay(duration)} - {discord.utils.format_dt(channel.created_at, style='D')}{discord.utils.format_dt(channel.created_at, style='t')} to {discord.utils.format_dt(discord.utils.utcnow(), style='t')}", color=self.client.embed_color)
                            print("Sanity check 22")
                            summary_embed.description = message_count
                            print("Sanity check 23")
                        else:
                            print("Sanity check 24")
                            summary_embed = discord.Embed(title="No summary to display.")
                            print("Sanity check 25")
                        await webh.send(username="Game Summary", embed=summary_embed, view=DeleteChannel())
                        print("Sanity check 26")









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