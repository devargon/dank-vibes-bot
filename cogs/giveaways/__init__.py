from .giveaways import Giveaways

def setup(client):
    client.add_cog(Giveaways(client))