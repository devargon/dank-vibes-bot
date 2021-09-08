from .messagetracking import MessageTracking

def setup(client):
    client.add_cog(MessageTracking(client))