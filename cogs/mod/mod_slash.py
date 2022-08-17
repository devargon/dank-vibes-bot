import datetime
import io
import time

import discord
from discord.ext import commands
from discord import SlashCommandGroup
from discord import default_permissions
from utils.format import stringtime_duration, human_join, comma_number, generate_loadbar, plural
from utils.buttons import confirm
from utils.time import humanize_timedelta
from utils import checks


class ModSlash(commands.Cog):
    def __init__(self, client):
        self.client = client

    mod_util = SlashCommandGroup("modutil", "Moderation Utility Commands")

    #@checks.has_permissions_or_role(manage_roles=True)
    @mod_util.command(name="dm")
    async def mod_dm(self, ctx: discord.ApplicationContext, user: discord.Member, message: discord.Option(str, max_length=2000)):
        embed = discord.Embed(title=f"You sent to {user}", description=message, color=self.client.embed_color)
        user_embed = discord.Embed(title="Message", description=message, color=discord.Color.purple(), timestamp=discord.utils.utcnow())
        try:
            await user.send(f"You have received a message from a Moderator in {ctx.guild.name}.", embed=user_embed)
        except discord.Forbidden:
            confirmview = confirm(ctx, self.client, timeout=30)
            confirmview.response = await ctx.respond(f"<:DVB_False:887589731515392000> **I was unable to DM {user}.**\nDo you want them to be pinged in <#698462922682138654> with the message instead?", view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is True:
                bot_lounge = discord.utils.get(ctx.guild.channels, name="╭・bot-lounge")
                if bot_lounge is not None:
                    await bot_lounge.send(f"{user.mention} You have received a message from a Moderator in {ctx.guild.name}.", embed=user_embed)
                    embed.title += f" via {bot_lounge.name}."
                    await ctx.respond(embed=embed)
                else:
                    await ctx.respond("Bot Lounge channel not found.")
        else:
            await ctx.respond(embed=embed)




    @default_permissions(administrator=True)
    @checks.has_permissions_or_role(administrator=True)
    @commands.slash_command(name="massban")
    async def massban(self, ctx: discord.ApplicationContext,
                      reason: discord.Option(str, "The reason for the ban."),
                      joined_after_duration: discord.Option(str, "Bans users that join after a time specified by DURATION. E.g. 30s means the time 30 seconds ago.") = None,
                      joined_before_duration: discord.Option(str, "Bans users that join before a time specified by DURATION. E.g. 30s means the time 30 seconds ago.") = None,
                      joined_after_timestamp: discord.Option(str, "Bans users that join after a TIMESTAMP.") = None,
                      joined_before_timestamp: discord.Option(str, "Bans users that join before a TIMESTAMP.") = None,
                      user_id_startswith: discord.Option(str, "Bans users that have a user ID starting with ___.") = None,
                      text_in_name: discord.Option(str, "Bans users that have a specified text in their username") = None,
                      ):
        if ctx.guild.id != 871734809154707467:
            return await ctx.respond("🏗️🚧 Command under construction.")
        if joined_after_duration is not None and joined_after_timestamp is not None:
            await ctx.respond("<:DVB_False:887589731515392000> You can't specify both `joined_after_duration` and `joined_after_timestamp`.")
            return
        if joined_before_duration is not None and joined_before_timestamp is not None:
            await ctx.respond("<:DVB_False:887589731515392000> You can't specify both `joined_before_duration` and `joined_before_timestamp`.")
            return
        if joined_after_duration is None and joined_after_timestamp is None and joined_before_duration is None and joined_before_timestamp is None and user_id_startswith is None and text_in_name is None:
            await ctx.respond("<:DVB_False:887589731515392000> You must specify at least one of the following: `joined_after_duration`, `joined_after_timestamp`, `joined_before_duration`, `joined_before_timestamp`, `user_id_startswith`, or `text_in_name`.")
            return
        if (joined_before_timestamp is not None or joined_before_duration is not None) and (joined_after_timestamp is None and joined_after_duration is None):
            await ctx.respond("<:DVB_False:887589731515392000> You must specify a `joined_after_timestamp`/`joined_after_duration` if you specify `joined_before_timestamp` or `joined_before_duration`.")
            return
        if joined_after_duration is not None:
            try:
                joined_after_duration: int = stringtime_duration(joined_after_duration)
            except ValueError:
                await ctx.respond("<:DVB_False:887589731515392000> You didn't provide a proper `joined_after_duration`.", ephemeral=True)
                return
            if joined_after_duration is None:
                await ctx.respond("<:DVB_False:887589731515392000> You didn't provide a proper `joined_after_duration`.", ephemeral=True)
                return
            joined_after_timestamp = round(time.time()) - joined_after_duration
        if joined_before_duration is not None:
            try:
                joined_before_duration: int = stringtime_duration(joined_before_duration)
            except ValueError:
                await ctx.respond("<:DVB_False:887589731515392000> You didn't provide a proper `joined_before_duration`.", ephemeral=True)
                return
            if joined_before_duration is None:
                await ctx.respond("<:DVB_False:887589731515392000> You didn't provide a proper `joined_before_duration`.", ephemeral=True)
                return
            joined_before_timestamp = round(time.time()) - joined_before_duration
        # joined_after cannot be more than 5 days ago
        # joined_before can only be used if join_after is specified
        if joined_after_timestamp is not None:
            joined_after_dt = datetime.datetime.fromtimestamp(int(joined_after_timestamp), datetime.timezone.utc)
        else:
            joined_after_dt = None
        if joined_before_timestamp is not None:
            joined_before_dt = datetime.datetime.fromtimestamp(int(joined_before_timestamp), datetime.timezone.utc)
        else:
            joined_before_dt = None
        if (joined_after_dt is not None and discord.utils.utcnow() < joined_after_dt) or (joined_before_dt is not None and discord.utils.utcnow() < joined_before_dt):
            return await ctx.respond("<:DVB_False:887589731515392000> You cannot specify a date/time in the future.")
        two_day_timedelta = datetime.timedelta(days=2)
        if joined_after_dt is not None:
            if discord.utils.utcnow() - joined_after_dt > two_day_timedelta:
                return await ctx.respond("<:DVB_False:887589731515392000> You cannot specify a date/time more than 2 days ago.")
        if joined_before_dt is not None:
            if discord.utils.utcnow() - joined_before_dt > two_day_timedelta:
                return await ctx.respond("<:DVB_False:887589731515392000> You cannot specify a date/time more than 2 days ago.")

        qualified_members = []
        for member in ctx.guild.members:
            joined_before_true = False
            joined_after_true = False
            userid_startswith_true = False
            text_in_name_true = False
            if joined_before_dt is not None:
                if member.joined_at < joined_before_dt:
                    joined_before_true = True
            else:
                joined_before_true = True
            if joined_after_dt is not None:
                if member.joined_at > joined_after_dt:
                    joined_after_true = True
            else:
                joined_after_true = True
            if user_id_startswith is not None:
                user_id = str(member.id)
                if user_id.startswith(user_id_startswith):
                    userid_startswith_true = True
            else:
                userid_startswith_true = True
            if text_in_name is not None:
                if text_in_name.lower() in member.name.lower():
                    text_in_name_true = True
            else:
                text_in_name_true = True
            if joined_before_true is True and joined_after_true is True and userid_startswith_true is True and text_in_name_true is True:
                if discord.utils.utcnow() - member.joined_at < two_day_timedelta:
                    qualified_members.append(member)
        qualified_description = []
        if joined_before_timestamp:
            qualified_description.append(f"• Joined before <t:{joined_before_timestamp}:f>")
        if joined_after_timestamp:
            qualified_description.append(f"• Joined after <t:{joined_after_timestamp}:f>")
        if user_id_startswith:
            qualified_description.append(f"• Has a User ID starting with `{user_id_startswith}...`")
        if text_in_name:
            qualified_description.append(f"• Has `{text_in_name}` in their user name")
        qualified_description.append(f"• Joined within the last two days")

        ids_only_str = ""
        ids_and_proper_str = ""
        files = []
        for member in qualified_members:
            ids_only_str += str(member.id) + "\n"
            ids_and_proper_str += f"{member.name} {member.id}\n"
        if len(qualified_members) == 0:
            ids_only, ids_and_proper = None, None
        else:
            ids_only = io.StringIO()
            ids_only.write(ids_only_str)
            ids_only.seek(0)
            ids_and_proper = io.StringIO()
            ids_and_proper.write(ids_and_proper_str)
            ids_and_proper.seek(0)
        if ids_only is not None:
            files.append(discord.File(ids_only, filename="ids_only.txt"))
        if ids_and_proper is not None:
            files.append(discord.File(ids_and_proper, filename="ids_and_proper.txt"))
        qualified_description = "I've done a check on members in the server who...\n\n" + "\n".join(qualified_description)
        qualified_description += f"\n\n**{plural(len(qualified_members)):member}** qualify the above requirements.\nThat makes up **{round((len(qualified_members)/len(ctx.guild.members))*100, 2)}%** q      of the server.\n"
        ## that makes up ...
        if len(qualified_members) > 0:
            qualified_description += f"\nThe list of members are in the files."
        confirm_embed = discord.Embed(title="Massban Confirmation", description=qualified_description, color=self.client.embed_color)
        if len(qualified_members) == 0:
            await ctx.respond(embed=confirm_embed)
            return
        if len(qualified_members) > 3000:
            confirm_embed.description += "\n<:DVB_False:887589731515392000> You are not allowed to ban more than 3000 members at once.'"
            await ctx.respond(embed=confirm_embed, files=files)
        else:
            confirm_embed.description += f"\nPress confirm to proceed to ban users."
            confirmview = confirm(ctx, self.client, 60.0)
            confirmview.response = await ctx.respond(embed=confirm_embed, files=files, view=confirmview)
            confirmview.stop()
            return
            await confirmview.wait()
            if confirmview.returning_value is not True:
                confirm_embed.color = discord.Color.red()
                confirm_embed.description.replace("Press confirm to proceed to ban users.", "No action was taken.")
                return await confirmview.response.edit_original_message(embed=confirm_embed)
            else:
                durations = []
                time_now = time.time()
                duration_now = time.perf_counter()
                status_embed = discord.Embed(title=f"Massban started")
                status_embed.description = f"[0/{len(qualified_members)}] {generate_loadbar(0, 15)} {round(0/len(qualified_members)*100, 2)}%"
                average_per = 0
                duration_remaining = average_per*(len(qualified_members)-len(durations))
                status_embed.add_field(name="Time remaining", value=f"{humanize_timedelta(seconds=round(duration_remaining))}\nComplete by: <t:{round(time.time())+round(duration_remaining)}>")
                status_msg = await ctx.send(embed=status_embed)
                for index, member in enumerate(qualified_members):
                    try:
                        await member.ban(reason=reason or f"Massban authorized by {ctx.author.name}")
                    except Exception as e:
                        await ctx.send(f"<:DVB_False:887589731515392000> Unable to ban {member}:\n{str(e)}")
                    if time.time() - time_now > 3:
                        time_now = time.time()
                        status_embed.description = f"`[{index}/{len(qualified_members)}]` {generate_loadbar(index/len(qualified_members), 15)} {round(index/len(qualified_members)*100, 2)}%"
                        average_per = sum(durations) / len(durations)
                        duration_remaining = average_per * (len(qualified_members) - len(durations))
                        status_embed.set_field_at(-1, name="Time remaining", value=f"{humanize_timedelta(seconds=round(duration_remaining))}\nComplete by: <t:{round(time.time())+round(duration_remaining)}>")
                        try:
                            await status_msg.edit(embed=status_embed)
                        except discord.NotFound:
                            status_msg = await ctx.send(embed=status_embed)
                    durations.append(time.perf_counter() - duration_now)
                    duration_now = time.perf_counter()

                status_embed.description = f"[{len(qualified_members)}/{len(qualified_members)}] {generate_loadbar(1, 15)} 100%"
                status_embed.set_field_at(-1, name="Time remaining", value=f"<:DVB_True:887589686808309791> Completed at <t:{round(time.time())}>")
                try:
                    await status_msg.edit(embed=status_embed)
                except discord.NotFound:
                    status_msg = await ctx.send(embed=status_embed)
                return await ctx.send(f"<:DVB_True:887589686808309791> Massban completed.")




















    @commands.slash_command(name='find', description="Use this command to find a user, channel or role (through autocomplete).")
    async def find_slash(self, ctx: discord.ApplicationContext,
                         user: discord.Option(discord.Member, "Find a member in the server.") = None,
                         role: discord.Option(discord.Role, "Find a role in the server.") = None,
                         text_channel: discord.Option(discord.TextChannel, "Find a TEXT channel in the server.") = None,
                         voice_channel: discord.Option(discord.VoiceChannel, "Find a VOICE channel in the server.") = None,
                         category_channel: discord.Option(discord.CategoryChannel, "Find a CATEGORY channel in the server.") = None,
                         stage_channel: discord.Option(discord.StageChannel, "Find a STAGE channel in the server.") = None
                         ):
        results = []
        if user is None and role is None and text_channel is None and voice_channel is None and category_channel is None and stage_channel is None:
            await ctx.respond("Did you just try to find... **Nothing**?\nSpecify a user, role, text channel, voice channel, category channel or stage channel that you're finding.", ephemeral=True)
            return
        if user is not None:
            if user.display_name == user.name:
                start = f"User found: **{user}** {user.id} {user.mention}\n```dv.wi {user.id}```"
            else:
                start = f"User found: **{user}** ({user.name}) {user.id} {user.mention}```dv.wi {user.id}```"
            results.append(start)
        if role is not None:
            start = f"Role found: **{role.name}** {role.id} {role.mention}```dv.ri {role.id}```"
            results.append(start)
        if text_channel is not None:
            start = f"Text channel found: **{text_channel.name}** {text_channel.id} {text_channel.mention}"
            results.append(start)
        if voice_channel is not None:
            start = f"Voice channel found: **{voice_channel.name}** {voice_channel.id} {voice_channel.mention}"
            results.append(start)
        if category_channel is not None:
            start = f"Category channel found: **{category_channel.name}** {category_channel.id}"
            results.append(start)
        if stage_channel is not None:
            start = f"Stage channel found: **{stage_channel.name}** {stage_channel.id}"
            results.append(start)
        await ctx.respond("\n".join(results), ephemeral=True)
