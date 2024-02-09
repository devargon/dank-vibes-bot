import re
from datetime import datetime

import amari
import discord
from discord.ext import commands
from pytz import timezone

from utils.format import durationdisplay, proper_userf
from utils.converters import MemberUserConverter
from utils.time import humanize_timedelta
from utils.format import comma_number
from time import time
from main import dvvt


def transform_external_url(original_url):
    # Check if 'mp:external' is in the URL and split accordingly
    if 'mp:external' in original_url:
        parts = original_url.split('mp:external/')
        identifier_and_external_link = parts[1]
    else:
        return original_url

    # Construct the new base URL
    new_base_url = "https://media.discordapp.net/external/"
    new_url = f"{new_base_url}{identifier_and_external_link}"

    # Regex to find a primary image extension followed by an additional extension
    pattern = r'\.(jpg|jpeg|png|gif)\.\w+$'
    new_url = re.sub(pattern, r'.\1', new_url)  # Replace the match with just the primary image extension

    return new_url


def spotify_embed(member: discord.Member):
    today = discord.utils.utcnow()
    activitylist = member.activities
    for activity in activitylist:
        if isinstance(activity, discord.Spotify):
            artists = ", ".join(activity.artists)
            spotify = discord.Embed(title=f"{member.name} is listening to",
                                    description=f"[{artists} - {activity.title}](https://open.spotify.com/track/{activity.track_id})",
                                    color=activity.color)
            spotify.set_author(name=proper_userf(member), icon_url=member.display_avatar.url)
            spotify.set_footer(text=f"Powered by Spotify®", icon_url="https://i.imgur.com/zNBmzpl.png")
            spotify.set_thumbnail(url=activity.album_cover_url)
            listenduration = today - activity.start
            listenduration = round(listenduration.total_seconds())
            songend = round(activity.duration.total_seconds())
            position = (listenduration / songend) * 20
            position = round(position)
            duration = "────────────────────"
            bar = f" ◄◄⠀▐▐⠀►► {durationdisplay(listenduration)} / {durationdisplay(songend)} ───○ 🔊"
            duration = list(duration)
            duration.insert(position, "⚪")
            duration = "".join(duration)
            spotify.add_field(name=duration, value=bar, inline=False)
            spotify.add_field(name="Song album", value=activity.album, inline=False)
            return spotify
    return None


def activity_embed(member: discord.Member):
    today = discord.utils.utcnow()
    activitylist = member.activities
    if not activitylist:
        return None
    for activity in activitylist:
        if isinstance(activity, discord.Game):
            activityembed = discord.Embed(title=f"{member.name} is playing:", color=member.color)
            activityembed.set_author(name=f"{proper_userf(member)}", icon_url=member.display_avatar.url)
            if activity.start:
                starttime = activity.start
                duration = today - activity.start
                duration = duration.total_seconds()
                start = f"Started playing at <t:{round(starttime.timestamp())}>\n<:Reply:871808167011549244> {humanize_timedelta(seconds=duration)} ago"
            else:
                start = ""
            if activity.end:
                starttime = activity.end
                duration = activity.end - today
                duration = duration.total_seconds()
                stop = f"\nWill stop playing at <t{round(starttime.timestamp())}>\n<:Reply:871808167011549244> {humanize_timedelta(seconds=duration)} later"
            else:
                stop = ""
            output = start + stop
            if output:
                output = output
            else:
                output = r"Nothing to show here ¯\_(ツ)_/¯"
            activityembed.add_field(name=activity.name, value=output, inline=False)
            return activityembed
        elif isinstance(activity, discord.Streaming):
            if activity.platform == "Twitch" or activity.platform not in ["YouTube", "Twitch"]:
                    platform, emoji = "Twitch", "<:DVB_Twitch:983024242104860842>"
            elif activity.platform == "YouTube":
                platform, emoji = "YouTube", "<:DVB_YouTube:983024271192379442>"
            activityembed = discord.Embed(title=f"{member.name} is streaming:",
                                          description=f'[{activity.name} on {platform}]({activity.url} "{activity.name} on {activity.platform}") {emoji}',
                                          color=member.color)
            activityembed.set_author(name=proper_userf(member), icon_url=member.display_avatar.url)
            activityembed.add_field(name="Steam details", value=f"Playing {activity.game}", inline=False)
            return activityembed
        elif isinstance(activity, discord.Activity):
            if activity.type == discord.ActivityType.unknown:
                activityembed = discord.Embed(title=f"{member.name} is playing:", description="**Unknown Activity**", color=member.color)
            elif activity.type == discord.ActivityType.custom:
                activityembed = discord.Embed(title=f"{member.name} is playing:", description=activity.name, color=member.color)
            elif activity.type == discord.ActivityType.listening:
                activityembed = discord.Embed(title=f"{member.name} is listening to:", description=activity.name, color=member.color)
            elif activity.type == discord.ActivityType.watching:
                activityembed = discord.Embed(title=f"{member.name} is watching:", description=activity.name, color=member.color)
            elif activity.type == discord.ActivityType.competing:
                activityembed = discord.Embed(title=f"{member.name} is competing in:", description=activity.name, color=member.color)
            elif activity.type == discord.ActivityType.playing:
                activityembed = discord.Embed(title=f"{member.name} is playing:", color=member.color)
                activityembed.set_author(name=proper_userf(member), icon_url=member.display_avatar.url)
                if activity.start:
                    starttime = activity.start
                    duration = today - activity.start
                    duration = duration.total_seconds()
                    start = f"Started playing at <t:{round(starttime.timestamp())}>\n<:Reply:871808167011549244> {humanize_timedelta(seconds=duration)} ago"
                else:
                    start = ""
                if activity.end:
                    starttime = activity.end
                    duration = activity.end - today
                    duration = duration.total_seconds()
                    stop = f"\nWill stop playing at <t:{round(starttime.timestamp())}>\n<:Reply:871808167011549244> {humanize_timedelta(seconds=duration)} later"
                else:
                    stop = ""
                keydetails = ""
                if activity.details:
                    keydetails += f"**{activity.details}**\n"
                if activity.state:
                    keydetails += f"**{activity.state}\n**"
                output = start + stop
                if output:
                    keydetails += output
                if activity.large_image_url:
                    activityembed.set_thumbnail(url=transform_external_url(activity.large_image_url))
                    if activity.small_image_url:
                        activityembed.set_footer(text=activity.small_image_text, icon_url=transform_external_url(activity.small_image_url))
                elif activity.small_image_url:
                    activityembed.set_thumbnail(url=transform_external_url(activity.small_image_url))

                activityembed.add_field(name=activity.name, value=keydetails, inline=False)
            else:
                activityembed = None
            return activityembed
    return None

class ViewUserProfile(discord.ui.View):
    def __init__(self, base_embed, spotify_embed, activity_embed):
        self.base_embed = base_embed
        self.spotify_embed = spotify_embed
        self.activity_embed = activity_embed
        super().__init__(timeout=None)

        class Toggle(discord.ui.Button):
            def __init__(self, embed, *args, **kwargs):
                self.embed = embed
                super().__init__(disabled = True if self.embed is None else False, *args, **kwargs)

            async def callback(self, interaction: discord.Interaction):
                for b in self.view.children:
                    if b == self:
                        b.style = discord.ButtonStyle.green
                    else:
                        b.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(embed=self.embed, view=self.view)

        self.add_item(Toggle(self.base_embed, emoji=discord.PartialEmoji.from_str('<:DVB_Profile:983027673209135104>'), style=discord.ButtonStyle.green))
        self.add_item(Toggle(self.spotify_embed, emoji=discord.PartialEmoji.from_str('<:DVB_Spotify:983025014934741012>')))
        self.add_item(Toggle(self.activity_embed, emoji=discord.PartialEmoji.from_str('<:DVB_Activity:983025521971568680>')))


class Whois(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.guild_only()
    @commands.command(name='whois', usage='<user>', aliases=['wi'])
    async def whois(self, ctx, *, user: MemberUserConverter = None):
        """
        Get information about a user.
        """
        if user is None:
            return await ctx.help()
            #return await ctx.send("idk who tf that is")
        created_on = user.created_at.strftime("%a, %b %d, %Y")
        description = ["**General**",
                f"• Username: **{str(user)}**",
                f"• User ID: **{user.id}**",
                f"• Account created on: **{created_on}**"]
        if (joined_at := getattr(user, 'joined_at', None)):
            joined_at = joined_at.strftime("%a, %b %d, %Y") if joined_at is not None else 'Unknown'
            description.append(f"• Joined server on: **{joined_at}**")
        else:
            description.append(f"• Not in server")
        if ctx.author.guild_permissions.kick_members and isinstance(user, discord.Member):
            description.append(f"• User is verified: {f'<:DVB_False:887589731515392000> They have **{humanize_timedelta(seconds=user.joined_at.timestamp()+86400-round(time()))}** to complete the Membership Screening.' if user.pending else '<:DVB_True:887589686808309791>'}")
        embed = discord.Embed(color=self.client.embed_color)
        embed.set_author(name="{}'s Information".format(user.name), icon_url=user.display_avatar.url)
        a = await self.client.fetch_amari_data(user.id, ctx.guild.id)
        user_amari = a[0]
        if isinstance(user_amari, amari.objects.User):
            amaridetails = [f"Level: **{user_amari.level}**",
                            f"XP: **{comma_number(user_amari.exp)}**",
                            f"Weekly XP: **{comma_number(user_amari.weeklyexp)}**",
                            f"Rank: **{comma_number(user_amari.position+1)}**"
                            ]
            embed.add_field(name=f"<:DVB_Amari:975377537658134528> Amari Data", value="\n".join(amaridetails))
        embed.set_thumbnail(url=user.display_avatar.url)
        if discord.utils.get(ctx.author.roles, id=608495204399448066) or discord.utils.get(ctx.author.roles, id=684591962094829569) or ctx.author.guild_permissions.manage_roles:
            embed.add_field(name="Past nicknames", value="Retrieving their past nicknames...", inline=False)
            embed.add_field(name="Past usernames", value="Retrieving their past usernames...", inline=False)
        embed.description = '\n'.join(description)
        if isinstance(user, discord.Member):
            sp_embed = spotify_embed(user)
            at_embed = activity_embed(user)
        else:
            sp_embed = None
            at_embed = None
        wiview = ViewUserProfile(embed, sp_embed, at_embed)
        uimessage = await ctx.send(embed=embed, view=wiview)
        if discord.utils.get(ctx.author.roles, id=608495204399448066) or discord.utils.get(ctx.author.roles, id=684591962094829569) or ctx.author.guild_permissions.manage_roles:
            past_nicknames = await self.client.db.fetch("SELECT * FROM nickname_changes WHERE member_id = $1 ORDER BY time DESC LIMIT 20", user.id)
            if past_nicknames:
                nicknames = []
                for nickname in past_nicknames:
                    if nickname.get('nickname'):
                        nicknames.append(nickname.get('nickname'))
                embed.set_field_at(-2, name="Nicknames", value=f"{', '.join(nicknames) if len(nicknames) > 0 else 'No records; nicknames are only tracked after 9 January 21.'}\n\nRun `nicknames @{proper_userf(user, False)}` to see their other nicknames and the time they were changed."[:1023], inline=False)
            else:
                embed.set_field_at(-2, name="Nicknames", value=f"No records", inline=False)
            past_names = await self.client.db.fetch("SELECT * FROM name_changes WHERE user_id = $1 ORDER BY time DESC LIMIT 20", user.id)
            if past_names:
                names = []
                for name in past_names:
                    if name.get('name'):
                        names.append(name.get('name'))
                    embed.set_field_at(-1, name="Usernames", value=f"{', '.join(names) if len(names) > 0 else 'No records; usernames are only tracked after 9 January 21.'}\n\nRun `names @{proper_userf(user, False)}` to see their after usernames and the time they were changed."[:1023], inline=False)
            else:
                embed.set_field_at(-1, name="Usernames", value=f"No records", inline=False)
            wiview.base_embed = embed
            await uimessage.edit(embed=embed)
