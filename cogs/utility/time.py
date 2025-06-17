import random
from datetime import datetime

import alexflipnote
import amari
import discord
import pytz
from discord import SlashCommandGroup
from discord.ext import commands
from pytz import timezone
from typing import Optional

from utils.format import durationdisplay, proper_userf
from utils.converters import MemberUserConverter
from utils.time import humanize_timedelta
from utils.format import comma_number
from time import time
from main import dvvt
from custom_emojis import DVB_TRUE, DVB_FALSE

def get_time_color(hour):
    if 0 <= hour < 4:
        return 0x002244  # Deep night
    elif 4 <= hour < 6:
        return 0x004488  # Approaching sunrise
    elif 6 <= hour < 8:
        return 0xFFA500  # Sunrise
    elif 8 <= hour < 16:
        return 0x87CEEB  # Daytime
    elif 16 <= hour < 18:
        return 0xFF4500  # Approaching sunset
    elif 18 <= hour < 20:
        return 0x004488  # Just after sunset
    else:
        return 0x002244  # Deep evening into night


async def timezone_autocomplete(ctx: discord.AutocompleteContext):
    user_input = ctx.options.get("zone", "").lower()

    # Current UTC time
    utc_now = discord.utils.utcnow()

    # Filter and format the timezones
    matching_timezones = []

    for tz in pytz.all_timezones:
        if user_input in tz.lower():
            local_time = utc_now.astimezone(pytz.timezone(tz))
            formatted_time = local_time.strftime("%I:%M %p")
            matching_timezones.append(f"{tz} - {formatted_time}")
    if not user_input:
        random.shuffle(matching_timezones)
    choices = matching_timezones[:24]
    choices.append("None")
    return choices

timezone_option = discord.Option(description="Select a timezone.", autocomplete=timezone_autocomplete)



class UserTime(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.alex_api = alexflipnote.Client()

    async def get_time_response(self, ctx, selected_member):
        content = None
        embeds = []
        files = []

        def generate_time_disp(timezone):
            local_time = discord.utils.utcnow().astimezone(pytz.timezone(timezone))

            # Formatting the time
            date_str = local_time.strftime("%d %B %Y")
            time_str = local_time.strftime("%I:%M %p")

            # Getting the UTC offset
            offset_seconds = local_time.utcoffset().total_seconds()
            hours, remainder = divmod(offset_seconds, 3600)
            minutes = remainder // 60
            offset_str = f"UTC {'+' if hours > 0 else '-'} {abs(int(hours)):02}:{abs(int(minutes)):02}"
            return f"{date_str}, **{time_str}** ({offset_str})"

        async def generate_time_embed(timezone, user: discord.Member):
            if timezone is None:
                if ctx.author == user:
                    description = "Use </time set:1144153317593854023> to set a timezone."
                else:
                    description = f"Tell {user.mention} to set a timezone with </time set:1144153317593854023>."
                embed = discord.Embed(title="No timezone set", description=description, colour=2829627)
            else:
                local_time = discord.utils.utcnow().astimezone(pytz.timezone(timezone))
                embed = discord.Embed(title=generate_time_disp(timezone), color=get_time_color(local_time.hour))
                embed.set_footer(text=timezone)
                embed.set_thumbnail(url=f"attachment://{user.id}.png")
            embed.set_author(name=proper_userf(user), icon_url=user.display_avatar)
            return embed



        ctx_userinfo = await self.client.fetch_user_info(ctx.author.id)
        ctx_user_timezone = ctx_userinfo.timezone

        if ctx_user_timezone is not None:
            ctx_user_time = discord.utils.utcnow().astimezone(pytz.timezone(ctx_user_timezone))
            img = await self.alex_api.clock_by_datetime(ctx_user_time)
            img_bytes = await img.read()
            files.append(discord.File(fp=img_bytes, filename=f"{ctx.author.id}.png"))
        embeds.append(await generate_time_embed(ctx_user_timezone, ctx.author))



        tgt_user_timezone = None
        if selected_member is not None:
            selected_userinfo = await self.client.fetch_user_info(selected_member.id)
            tgt_user_timezone = selected_userinfo.timezone
            if tgt_user_timezone is not None:
                tgt_user_time = discord.utils.utcnow().astimezone(pytz.timezone(tgt_user_timezone))
                img = await self.alex_api.clock_by_datetime(tgt_user_time)
                img_bytes = await img.read()
                files.append(discord.File(fp=img_bytes, filename=f"{selected_member.id}.png"))
            embeds.append(await generate_time_embed(tgt_user_timezone,selected_member))

        if ctx_user_timezone is not None and tgt_user_timezone is not None:

            tgt_offset_seconds = tgt_user_time.utcoffset().total_seconds()
            ctx_offset_seconds = ctx_user_time.utcoffset().total_seconds()

            # Find the difference in hours
            time_difference = (tgt_offset_seconds - ctx_offset_seconds) / 3600

            if time_difference > 0:
                diff_str = f"**{selected_member.name}** is **{int(time_difference)}** hours ahead of you."
            elif time_difference < 0:
                diff_str = f"**{selected_member.name}** is **{int(-time_difference)}** hours behind you."
            else:
                diff_str = f"You and **{selected_member.name}** are in the same timezone."

            embeds.append(discord.Embed(description=diff_str, color=2829627))
        return content, embeds, files

    @commands.guild_only()
    @commands.group(name='time')
    async def time_g(self, ctx, *, member: discord.Member = None):
        """
        Show yours or another user's time.
        """
        c, es, files = await self.get_time_response(ctx, member)
        await ctx.send(c, embeds=es, files=files)

    time_group = SlashCommandGroup("time", "Configure your timezone and show your time to others")

    @time_group.command(name="show", description="Show your current time or another user's time.")
    async def time_show_slash(self, ctx, member: discord.Option(discord.Member, description="Pick an optional member to see their time.", required=False)):
        c, es, files = await self.get_time_response(ctx, member)
        await ctx.respond(c, embeds=es, files=files)

    @time_group.command(name="set", description="Set your timezone for us to show your current time.")
    async def time_set_slash(self, ctx: discord.ApplicationContext, zone: timezone_option):
        if zone.lower() == "none":
            zone = None
        if zone is not None:
            selected_timezone = zone.split(" - ")[0]
            if selected_timezone not in pytz.all_timezones:
                return await ctx.respond(f"{DVB_FALSE} I could not find the timezone **{selected_timezone}**.")

            local_time = discord.utils.utcnow().astimezone(pytz.timezone(selected_timezone))
            formatted_time = local_time.strftime("%I:%M %p")

            response = f"{DVB_TRUE} Your timezone is set to **{selected_timezone}**. The current time there is **{formatted_time}**."
        else:
            selected_timezone = None
            response = f"{DVB_FALSE} Your timezone has been removed."
        ui = await self.client.fetch_user_info(ctx.author.id)
        ui.timezone = selected_timezone
        await self.client.update_user_info(ui)
        await ctx.respond(response)



