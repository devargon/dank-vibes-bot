from .help import Help

def setup(client):
    client.add_cog(Help(client))