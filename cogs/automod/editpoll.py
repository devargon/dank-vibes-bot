import asyncio

import discord
from discord.ext import commands, tasks
import time

from main import dvvt
from utils.format import generate_loadbar
from typing import Optional


class EditContent:
    __slots__ = ('content', 'embed', 'embeds')

    def __init__(self, content, embed, embeds):
        self.content: str = content
        self.embed: discord.Embed = embed
        self.embeds: list = embeds

    def __repr__(self) -> str:
        return f"<EditContent content={self.content} embed={self.embed} embeds={self.embeds}>"


class polledition(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    def generate_embed(self, author: str, author_icon: Optional[str], poll_name: str, polldata: dict):
        embed = discord.Embed(title=poll_name, color=self.client.embed_color)
        embed.set_footer(text="The poll data updates every 15 seconds.")
        if author_icon is not None:
            embed.set_author(name=author, icon_url=author_icon)
        else:
            embed.set_author(name=author)
        total = sum([polldata[key] for key in polldata])
        for index, key in enumerate(polldata):
            if polldata[key] == 0:
                progress_bar = generate_loadbar(0, length=8)
                percent = 0
            else:
                progress_bar = generate_loadbar(polldata[key] / total, length=8)
                percent = round(polldata[key]/total*100, 1)
            embed.add_field(name=f"{key} ({polldata[key]} votes)", value=f"{progress_bar} {percent}%", inline=False)
        return embed

    @tasks.loop(seconds=5)
    async def edit_polls(self):
        try:
            await self.client.wait_until_ready()
            time_past_expiry = round(time.time()) - 20*24*60*60
            polls = await self.client.pool_pg.fetch("SELECT * FROM polls WHERE created > $1", time_past_expiry)
            for poll in polls:
                creator_id = poll.get('creator_id')
                guild_id = poll.get('guild_id')
                channel_id = poll.get('channel_id')
                message_id = poll.get('message_id')
                poll_id = poll.get('poll_id')
                creator = self.client.get_user(creator_id)
                guild: discord.Guild = self.client.get_guild(guild_id)
                if guild is not None:
                    channel: discord.TextChannel = guild.get_channel(channel_id)
                    if channel is not None:
                        if creator is None:
                            author_icon, author_name = None, "Poll"
                        else:
                            author_icon, author_name = creator.display_avatar.url, f"{creator}'s Poll"
                        question = poll.get('poll_name')
                        choices = poll.get('choices').split('|')
                        polldata = await self.client.pool_pg.fetch("SELECT * FROM pollvotes WHERE poll_id = $1", poll_id)
                        poll_dict = {}
                        for choice in choices:
                            poll_dict[choice] = 0
                        for polled in polldata:
                            poll_dict[polled.get('choice')] += 1
                        embed = self.generate_embed(author_name, author_icon, question, poll_dict)

                        # For some reason I am unable to edit the message if the embed is enclosed in another object, for now this function will be used for embeds only
                        partial_message: discord.PartialMessage = channel.get_partial_message(message_id)
                        if discord.utils.get([m[0] for m in self.client.editqueue], id=partial_message.id) is not None:
                            #print('item already in queue')
                            continue
                        self.client.editqueue.append((partial_message, embed))
                        #print('added item to queue, queue:', self.client.editqueue)
        except Exception as e:
            print(f"timer task caught a error: {e}")
