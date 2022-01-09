from .disboard import DisboardAutoLock

def setup(client):
    client.add_cog(DisboardAutoLock(client))