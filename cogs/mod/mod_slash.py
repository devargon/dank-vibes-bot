import discord
from discord.ext import commands
from discord import default_permissions
from utils.format import stringtime_duration
from utils import checks


class ModSlash(commands.Cog):
    def __init__(self, client):
        self.client = client

    @default_permissions(manage_roles=True)
    @checks.has_permissions_or_role(manage_roles=True)
    @commands.slash_command(name="massban")
    async def massban(self, ctx: discord.ApplicationContext,
                      joined_after_duration: discord.Option(str, "Bans users that join after a time specified by DURATION.") = None,
                      joined_before_duration: discord.Option(str, "Bans users that join before a time specified by DURATION.") = None,
                      joined_after_timestamp: discord.Option(str, "Bans users that join after a TIMESTAMP.") = None,
                      joined_before_timestamp: discord.Option(str, "Bans users that join before a TIMESTAMP.") = None,
                      user_id_startswith: discord.Option(str, "Bans users that have a user ID starting with ___.") = None,
                      text_in_name: discord.Option(str, "Bans users that have a specified text in their username") = None
                      ):
        return await ctx.respond("🏗️🚧 Command under construction.")
        if joined_after_duration is not None and joined_after_timestamp is not None:
            await ctx.respond("You can't specify both `joined_after_duration` and `joined_after_timestamp`.")
            return
        if joined_before_duration is not None and joined_before_timestamp is not None:
            await ctx.respond("You can't specify both `joined_before_duration` and `joined_before_timestamp`.")
            return
        if joined_after_duration is not None:
            try:
                joined_after_duration: int = stringtime_duration(joined_after_duration)
            except ValueError:
                await ctx.respond("You didn't provide a proper joined_after_duration.", ephemeral=True)
                return
            if joined_after_duration is None:
                await ctx.respond("You didn't provide a proper joined_after_duration.", ephemeral=True)
                return
        if joined_before_duration is not None:
            try:
                joined_before_duration: int = stringtime_duration(joined_before_duration)
            except ValueError:
                await ctx.respond("You didn't provide a proper joined_before_duration.", ephemeral=True)
                return
            if joined_before_duration is None:
                await ctx.respond("You didn't provide a proper joined_before_duration.", ephemeral=True)
                return



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
