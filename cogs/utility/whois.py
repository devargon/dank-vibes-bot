import discord
from discord.ext import commands
from utils.converters import MemberUserConverter
from utils.time import humanize_timedelta
from time import time

class Whois(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.guild_only()
    @commands.command(name='whois', usage='<user>', aliases=['wi'])
    async def whois(self, ctx, user: MemberUserConverter = None):
        """
        Get information about a user.
        """
        if user is None:
            return await ctx.send("idk who tf that is")
        created_on = user.created_at.strftime("%a, %b %d, %Y")
        description = ["**General**",
                f"• Username: **{str(user)}**",
                f"• User ID: **{user.id}**",
                f"• Account created on: **{created_on}**"]
        if (joined_at := getattr(user, 'joined_at', None)):
            joined_at = joined_at.strftime("%a, %b %d, %Y") if joined_at is not None else 'Unknown'
            description.append(f"• Joined server on: **{joined_at}**")
        if ctx.author.guild_permissions.kick_members and isinstance(user, discord.Member):
            description.append(f"• User is verified: {f'<:DVB_False:887589731515392000> They have **{humanize_timedelta(seconds=user.joined_at.timestamp()+86400-round(time()))}** to complete the Membership Screening.' if user.pending else '<:DVB_True:887589686808309791>'}")
        embed = discord.Embed(color=self.client.embed_color)
        embed.set_author(name="{}'s Information".format(user.name), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.description = '\n'.join(description)
        await ctx.send(embed=embed)