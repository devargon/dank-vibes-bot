from .slashtags import SlashTags


def setup(client):
    client.add_cog(SlashTags(client))
