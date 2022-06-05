import discord
from utils.specialobjects import ServerConfiguration


def check_status(status: str, settings: ServerConfiguration) -> bool:
    if settings.statusmatchtype.lower() == "strict":
        return status == settings.statustext
    elif settings.statusmatchtype.lower() == "contains":
        return settings.statustext in status

def get_custom_activity(member: discord.Member) -> discord.CustomActivity:
    for activity in member.activities:
        if isinstance(activity, discord.CustomActivity):
            return activity
    return None