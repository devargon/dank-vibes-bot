from .mod import Mod

def setup(client):
    client.add_cog(Mod(client))