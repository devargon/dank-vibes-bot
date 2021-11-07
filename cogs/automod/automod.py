import discord
from discord.ext import commands
from .freezenick import Freezenick
from .verification import Verification
class AutoMod(Verification, Freezenick, commands.Cog):
    """
    This file is just a placeholder for the various automod functions/modules.
    """
    def __init__(self, client):
        self.client = client
        self.freezenick.start()
        self.check_verification.start()

    def cog_unload(self) -> None:
        self.freezenick.stop()
        self.check_verification.stop()