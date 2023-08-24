import random
from datetime import datetime

import amari
import discord
import pytz
from discord import SlashCommandGroup
from discord.ext import commands
from pytz import timezone

from utils.format import durationdisplay, proper_userf
from utils.converters import MemberUserConverter
from utils.time import humanize_timedelta
from utils.format import comma_number
from time import time
from main import dvvt


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

    async def get_time_response(self, ctx, selected_member):

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

        ctx_userinfo = await self.client.fetch_user_info(ctx.author.id)
        ctx_user_timezone = ctx_userinfo.timezone

        if ctx_user_timezone is not None:
            ctx_user_time_disp = generate_time_disp(ctx_user_timezone)

        tgt_user_timezone = None
        if selected_member is not None:
            selected_userinfo = await self.client.fetch_user_info(selected_member.id)
            tgt_user_timezone = selected_userinfo.timezone
            if tgt_user_timezone is not None:
                tgt_user_time_disp = generate_time_disp(tgt_user_timezone)



        if ctx_user_timezone is None:
            if selected_member is None:
                return "You have not set a timezone. Run </time set:1144153317593854023> to set it."
            else:
                if tgt_user_timezone is None:
                    return f"Both you and **{selected_member.name}** have not set a timezone."
                else:
                    return f"**{selected_member.name}**'s current timezone is **{tgt_user_timezone}**, the time there is {tgt_user_time_disp}. You have not set a timezone."

        if ctx_user_timezone is not None:
            # Getting the current local time in the specified timezone


            if selected_member is None:
                return f"Your current timezone is **{ctx_user_timezone}**.\nThe current time is {ctx_user_time_disp}."
            else:
                if tgt_user_timezone is not None:
                    tgt_local_time = discord.utils.utcnow().astimezone(pytz.timezone(tgt_user_timezone))
                    local_time = discord.utils.utcnow().astimezone(pytz.timezone(ctx_user_timezone))

                    tgt_offset_seconds = tgt_local_time.utcoffset().total_seconds()
                    ctx_offset_seconds = local_time.utcoffset().total_seconds()

                    # Find the difference in hours
                    time_difference = (tgt_offset_seconds - ctx_offset_seconds) / 3600

                    if time_difference > 0:
                        diff_str = f"**{selected_member.name}** is **{int(time_difference)}** hours ahead of you."
                    elif time_difference < 0:
                        diff_str = f"**{selected_member.name}** is **{int(-time_difference)}** hours behind you."
                    else:
                        diff_str = f"You and **{selected_member.name}** are in the same timezone."

                    return (
                        f"Your current timezone is **{ctx_user_timezone}**, the time is {ctx_user_time_disp}.\n"
                        f"**{selected_member.name}**'s current timezone is **{tgt_user_timezone}** and the time there is {tgt_user_time_disp}.\n{diff_str}")
                else:
                    return f"Your current timezone is **{ctx_user_timezone}**, the time is {ctx_user_time_disp}.\n**{selected_member.name}** has not set a timezone."

        return "An unexpected error occurred."  # Fallback response

    @commands.guild_only()
    @commands.group(name='time')
    async def time(self, ctx, *, member: discord.Member = None):
        """
        Show yours or another user's time.
        """
        c = await self.get_time_response(ctx, member)
        await ctx.send(c)


    time_group = SlashCommandGroup("time", "Configure your timezone and show your time to others")

    @time_group.command(name="show", description="Show your current time or another user's time.")
    async def time_show_slash(self, ctx, member: discord.Option(discord.Member, description="Pick an optional member to see their time.", required=False)):
        c = await self.get_time_response(ctx, member)
        await ctx.respond(c)

    @time_group.command(name="set", description="Set your timezone for us to show your current time.")
    async def time_set_slash(self, ctx: discord.ApplicationContext, zone: timezone_option):
        if zone.lower() == "none":
            zone = None
        if zone is not None:
            selected_timezone = zone.split(" - ")[0]
            if selected_timezone not in pytz.all_timezones:
                return await ctx.respond(f"<:DVB_False:887589731515392000> I could not find the timezone **{selected_timezone}**.")

            local_time = discord.utils.utcnow().astimezone(pytz.timezone(selected_timezone))
            formatted_time = local_time.strftime("%I:%M %p")

            response = f"<:DVB_True:887589686808309791> Your timezone is set to **{selected_timezone}**. The current time there is **{formatted_time}**."
        else:
            selected_timezone = None
            response = f"<:DVB_False:887589731515392000> Your timezone has been removed."
        ui = await self.client.fetch_user_info(ctx.author.id)
        ui.timezone = selected_timezone
        await self.client.update_user_info(ui)
        await ctx.respond(response)



