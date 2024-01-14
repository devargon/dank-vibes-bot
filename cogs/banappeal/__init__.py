from .banappeal import BanAppeal
def setup(client):
    client.add_cog(BanAppeal(client))