from .payout import PayoutManagement

def setup(client):
    client.add_cog(PayoutManagement(client))