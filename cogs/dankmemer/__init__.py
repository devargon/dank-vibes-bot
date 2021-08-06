from .dankmemer import DankMemer

def setup(client):
    client.add_cog(DankMemer(client))