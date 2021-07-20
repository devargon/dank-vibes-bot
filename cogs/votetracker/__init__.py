from .votetracker import VoteTracker

def setup(client):
    client.add_cog(VoteTracker(client))