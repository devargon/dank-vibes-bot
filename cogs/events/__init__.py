from .events import Events


def setup(client):
    client.add_cog(Events(client))
