from .utility import Utility

def setup(client):
    client.add_cog(Utility(client))