from .banbattle import BanBattle

def setup(client):
    client.add_cog(BanBattle(client))