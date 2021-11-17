import discord
from discord.ext import commands
from .freezenick import Freezenick
from .verification import Verification
from .timedrole import timedrole
class AutoMod(timedrole, Verification, Freezenick, commands.Cog):
    """
    This file is just a placeholder for the various automod functions/modules.
    """
    def __init__(self, client):
        self.client = client
        self.freezenick.start()
        self.check_verification.start()
        self.timedrole.start()

    def cog_unload(self) -> None:
        self.freezenick.stop()
        self.check_verification.stop()
        self.timedrole.stop()