from .on_message_two import AIMessageModeration


def setup(client):
    client.add_cog(AIMessageModeration(client))
