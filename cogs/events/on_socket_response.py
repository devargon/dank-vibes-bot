import discord
from main import dvvt
from discord.ext import commands
class SocketResponse(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, payload):
        print(f"Socket response payload received\nType: {type(payload)}\nPayload: {type(payload)}")