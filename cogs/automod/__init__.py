from .automod import AutoMod

def setup(client):
    client.add_cog(AutoMod(client))
