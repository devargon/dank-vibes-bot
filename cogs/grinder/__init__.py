from .grinderutils import Grinderutils

def setup(client):
    client.add_cog(Grinderutils(client))