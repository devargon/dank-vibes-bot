from .infection import infection

def setup(client):
    client.add_cog(infection(client));