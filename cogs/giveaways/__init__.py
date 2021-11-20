from .giveaways import giveaways

def setup(client):
    client.add_cog(giveaways(client))