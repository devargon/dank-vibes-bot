import discord
from discord.ext import commands
from .freezenick import Freezenick

class AutoMod(Freezenick, commands.Cog):
    """
    This file is just a placeholder for the various automod functions/modules.
    """
    def __init__(self, client):
        self.client = client
        self.freezenick.start()

    def cog_unload(self) -> None:
        self.freezenick.stop()