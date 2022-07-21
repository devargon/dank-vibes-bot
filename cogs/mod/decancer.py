import asyncio
import random
import re
import unicodedata
from datetime import datetime, timedelta
from main import dvvt
from utils.context import DVVTcontext
import stringcase
import unidecode
import discord
from discord.ext import commands

from utils import checks


class Decancer(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @staticmethod
    def is_cancerous(text: str) -> bool:
        for segment in text.split():
            for char in segment:
                if not (char.isascii() and char.isalnum()):
                    return True
        return False

    # the magic
    @staticmethod
    def strip_accs(text):
        try:
            text = unicodedata.normalize("NFKC", text)
            text = unicodedata.normalize("NFD", text)
            text = unidecode.unidecode(text)
            text = text.encode("ascii", "ignore")
            text = text.decode("utf-8")
        except Exception as e:
            print(e)
        return str(text)

    # the magician
    async def nick_maker(self, guild: discord.Guild, old_shit_nick):
        old_shit_nick = self.strip_accs(old_shit_nick)
        new_cool_nick = re.sub("[^a-zA-Z0-9 \n.]", "", old_shit_nick)
        new_cool_nick = " ".join(new_cool_nick.split())
        new_cool_nick = stringcase.lowercase(new_cool_nick)
        new_cool_nick = stringcase.titlecase(new_cool_nick)
        if len(new_cool_nick.replace(" ", "")) <= 1 or len(new_cool_nick) > 32:
            new_cool_nick = "simp name"
        return new_cool_nick

    async def decancer_log(
        self,
        guild: discord.Guild,
        member: discord.Member,
        moderator: discord.Member,
        old_nick: str,
        new_nick: str,
        dc_type: str,
    ):
        serverconfig = await self.client.get_guild_settings(guild.id)
        channel = guild.get_channel(serverconfig.modlog_channel)
        if not channel or not (
            channel.permissions_for(guild.me).send_messages
            and channel.permissions_for(guild.me).embed_links
        ):
            return
        color = self.client.embed_color
        description = [
            f"**Offender:** {member} {member.mention}",
            f"**Reason:** Remove cancerous characters from previous name",
            f"**New Nickname:** {new_nick}",
            f"**Responsible Moderator:** {moderator} {moderator.mention}",
        ]
        embed = discord.Embed(
            color=discord.Color(color),
            title=dc_type,
            description="\n".join(description),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

    @commands.command(name="decancer", aliases=['dc'])
    @checks.has_permissions_or_role(manage_roles=True)
    @commands.guild_only()
    async def nick_checker(self, ctx: DVVTcontext, user: discord.Member):
        """
        Remove special/cancerous characters from user nicknames
        Change username glyphs (i.e 乇乂, 黑, etc)
        special font chars (zalgo, latin letters, accents, etc)
        to their unicode counterpart. If the former, expect the "english"
        equivalent to other language based glyphs.
        """
        if user.top_role >= ctx.me.top_role:
            return await ctx.send(f"I can't decancer that user since they are higher than me in heirarchy.")
        m_nick = user.display_name
        new_cool_nick = await self.nick_maker(ctx.guild, m_nick)
        if m_nick != new_cool_nick:
            await user.edit(reason=f"Old name ({m_nick}): contained special characters", nick=new_cool_nick)
            await ctx.send(f"<:DVB_True:887589686808309791> {user}'s name **{m_nick}** was changed to **{new_cool_nick}**.")
            guild = ctx.guild
            await self.decancer_log(guild, user, ctx.author, m_nick, new_cool_nick, "Manual Decancer 👷‍♂️")
            try:
                await ctx.checkmark()
            except discord.NotFound:
                pass
        else:
            await ctx.send(f"<:DVB_False:887589731515392000> {user.display_name}'s name was already decancered.")
