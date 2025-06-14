from .actions import Actions

def setup(client):
    client.add_cog(Actions(client))