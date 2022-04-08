import discord
from discord.ext import commands

import os
import re
import time
disboard_channel = 630898540155240480 if os.getenv('state') == '0' else 871737314831908974
disboard_bot = 302050872383242240 if os.getenv('state') == '0' else 235148962103951360

class DisboardAutoLock(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            return
        if not message.author.id == disboard_bot:
            return
        if not len(message.embeds) > 0:
            return
        embed = message.embeds[0]
        if not embed.description:
            return
        dischannel = self.client.get_channel(disboard_channel)
        overwrite = dischannel.overwrites_for(message.guild.default_role)
        if overwrite.send_messages != False:
            if "Bump done!" in embed.description:
                if not message.channel.id == disboard_channel:
                    await dischannel.send(f"This server has been bumped by someone in another channel! Thank you for bumping the server <#")
                else:
                    await dischannel.send(f"Thank you for bumping the server ❤️ <3")
                now = round(time.time())
                timetobump = now + 7200
            else:
                regex2 = re.compile(f'<@.+> Please wait another (\d+) minute?s until the server can be bumped')
                result = re.findall(regex2, embed.description)
                if result:
                    if not message.channel.id == disboard_channel:
                        await dischannel.send(f"This server has been bumped by someone in another channel! Thank you for bumping the server!")
                    else:
                        await dischannel.send(f"Thank you for bumping the server ❤️ <3")
                now = round(time.time())
                if len(result) < 1:
                    return
                timetobump = now + int(result[0]) * 60
            overwrite.send_messages = False
            await dischannel.set_permissions(message.guild.default_role, overwrite=overwrite, reason=f"Disboard Auto Lock from bump by {message.author}")
            result = await self.client.db.fetchrow("SELECT * FROM timedunlock WHERE guild_id = $1 AND channel_id = $2", message.guild.id, disboard_channel)
            if result:
                await self.client.db.execute("UPDATE timedunlock SET time = $1 WHERE guild_id = $2 AND channel_id = $3 AND responsible_moderator = $4", timetobump, message.guild.id, disboard_channel, self.client.user.id)
            else:
                await self.client.db.execute("INSERT INTO timedunlock (guild_id, channel_id, time, responsible_moderator) VALUES ($1, $2, $3, $4)", message.guild.id, disboard_channel, timetobump, self.client.user.id)
        else:
            return






