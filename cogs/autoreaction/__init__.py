from discord import client
from .autoreactor import Autoreaction

def setup(client):
    client.add_cog(Autoreaction(client))