from .admin import Admin

def setup(client):
    client.add_cog(Admin(client))