from .donations import donations


def setup(client):
    client.add_cog(donations(client))