from .banappealcog import BanAppealCog
def setup(client):
    client.add_cog(BanAppealCog(client))