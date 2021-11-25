import os
import discord
from discord.ext import commands

class Censor(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if await self.client.check_blacklisted_content(message.content):
            async def get_messages():
                strbuffer = ""
                async for i in message.channel.history(limit=3):
                    print(i.content)
                    strbuffer += f"{i.author}: {i.content[:50] + '...' if len(i.content) > 50 else i.content}\n"
                    if i.author == message.author and i.content == message.content:
                        return strbuffer
                strbuffer += f"**{message.author}: {message.content[:50] + '...' if len(message.content) > 50 else message.content}**"
                return strbuffer
            try:
                await message.delete()
            except:
                pass
            channelid = 616007729718231161 if os.getenv('state') == '0' else 871737314831908974
            channel = self.client.get_channel(channelid)
            await channel.send(f"{message.author} ({message.author.id}) just said a blacklisted word", embed=discord.Embed(title="Jump to message", url=message.jump_url, description=await get_messages(), color=self.client.embed_color))
