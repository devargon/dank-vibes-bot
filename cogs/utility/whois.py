import discord
import contextlib
from discord.ext import commands
from utils.converters import MemberUserConverter

class Whois(commands.Cog):
    def __init__(self, client):
        self.client = client

    badges = {
            'bug_hunter': '<:bug_hunter:846149098893082634>',
            'bug_hunter_level_2': '<:bug_hunter_level_2:846149133823901717>',
            'early_supporter': '<:early_supporter:846149360572170261>',
            'hypesquad': '<:hypesquad:846149064227815475>',
            'hypesquad_balance': '<:hypesquad_balance:846149275876065320>',
            'hypesquad_bravery': '<:hypesquad_bravery:846149177284100107>',
            'hypesquad_brilliance': '<:hypesquad_brilliance:846149226244472842>',
            'partner': '<:partner:846154568517681152>',
            'staff': '<:staff:846149026785394719>',
            'verified_bot_developer': '<:verified_bot_developer:846148978575540245>'
            }

    @commands.guild_only()
    @commands.command(name='whois', usage='<user>')
    async def whois(self, ctx, user: MemberUserConverter = None):
        """
        Get information about a user.
        """
        if user is None:
            return await ctx.send("idk who tf is that")
        created_on = user.created_at.strftime("%a, %b %d, %Y")
        description = ["**General**",
                f"• Username: **{str(user)}**",
                f"• User ID: **{user.id}**",
                f"• Account created on: **{created_on}**"]
        badges = []
        for name, value in user.public_flags:
            if value:
                with contextlib.suppress(KeyError):
                    emoji = self.badges[name]
                    badges.append(emoji)
        if badges:
            description.append("• Badges: {}".format(' '.join(badges)))
        embed = discord.Embed(color=self.client.embed_color)
        embed.set_author(name="{}'s Information".format(user.name), icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = '\n'.join(description)
        await ctx.send(embed=embed)