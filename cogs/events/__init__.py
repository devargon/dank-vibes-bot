from .on_message import on_message


def setup(client):
    client.add_cog(on_message(client))
