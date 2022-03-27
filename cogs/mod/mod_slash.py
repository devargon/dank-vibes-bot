import discord
from discord.ext import commands

class ModSlash(commands.Cog):
    def __init__(self, client):
        self.client = client

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