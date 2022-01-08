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
    async def whois(self, ctx, *, user: MemberUserConverter = None):
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
        infection = await self.client.pool_pg.fetchrow("SELECT infectioncase, member_id, infector, timeinfected FROM infections WHERE member_id = $1", user.id)
        if infection:
            infector = self.client.get_user(infection.get('infector')) or infection.get('infector')
            description.append(f"• User is infected with CoviDVBot: 🤒 (Case **{infection.get('infectioncase')}**)\n<:Reply:871808167011549244> Infected by **{infector}** <t:{infection.get('timeinfected')}:R>")
        else:
            description.append("• User is infected with CoviDVBot: <:DVB_False:887589731515392000>")
        embed = discord.Embed(color=self.client.embed_color)
        embed.set_author(name="{}'s Information".format(user.name), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Past nicknames", value="Retrieving their past nicknames...", inline=False)
        embed.add_field(name="Past usernames", value="Retrieving their past usernames...", inline=False)
        embed.description = '\n'.join(description)
        uimessage = await ctx.send(embed=embed)
        past_nicknames = await self.client.pool_pg.fetch("SELECT * FROM nickname_changes WHERE member_id = $1 ORDER BY time DESC LIMIT 20", user.id)
        if past_nicknames:
            nicknames = []
            for nickname in past_nicknames:
                if nickname.get('nickname'):
                    nicknames.append(nickname.get('nickname'))
            embed.set_field_at(-2, name="Nicknames", value=f"{', '.join(nicknames) if len(nicknames) > 0 else 'No records; nicknames are only tracked after x January 21.'}\n\nRun `nicknames @{user}` to see their other nicknames and the time they were changed.", inline=False)
        else:
            embed.set_field_at(-2, name="Nicknames", value=f"No records; nicknames are only tracked after x January 21.", inline=False)
        past_names = await self.client.pool_pg.fetch("SELECT * FROM name_changes WHERE user_id = $1 ORDER BY time DESC LIMIT 20", user.id)
        if past_names:
            names = []
            for name in past_names:
                if name.get('name'):
                    names.append(name.get('name'))
                embed.set_field_at(-1, name="Usernames", value=f"{', '.join(names) if len(names) > 0 else 'No records; usernames are only tracked after x January 21.'}\n\nRun `names @{user}` to see their after usernames and the time they were changed.", inline=False)
        else:
            embed.set_field_at(-1, name="Usernames", value=f"No records; usernames are only tracked after x January 21.", inline=False)
        await uimessage.edit(embed=embed)