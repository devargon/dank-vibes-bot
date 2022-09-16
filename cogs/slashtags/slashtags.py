import discord
from discord.ext import commands
from discord import SlashCommandGroup
from .heist import HeistTags
from .privchannel import PrivChannelTags
from main import dvvt


class SlashTags(HeistTags, PrivChannelTags, commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
