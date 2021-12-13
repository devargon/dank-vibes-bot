from .christmas import Christmas


def setup(client):
    client.add_cog(Christmas(client))
