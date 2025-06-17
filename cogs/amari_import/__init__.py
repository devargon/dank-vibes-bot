from .amari_import import AmariImport

def setup(client):
    client.add_cog(AmariImport(client))
