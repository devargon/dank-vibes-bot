import asyncpg
from utils.format import split_string_into_list
import json


class GiveawayMessageNotFound(Exception):
    pass

class GiveawayChannelNotFound(Exception):
    pass

class GiveawayGuildNotFound(Exception):
    pass

class GiveawayConfig:
    __slots__ = ('guild_id', 'channel_id', 'bypass_roles', 'blacklisted_roles', 'multi')

    def __init__(self, record: asyncpg.Record):
        if record is None:
            self.guild_id, self.channel_id, self.bypass_roles, self.blacklisted_roles, self.multi = None, None, None, None, None
        else:
            self.guild_id = record['guild_id']
            self.channel_id = record['channel_id']
            self.bypass_roles = split_string_into_list(record['bypass_roles'], return_type=int)
            self.blacklisted_roles = split_string_into_list(record['blacklisted_roles'], return_type=int)
            if self.multi is not None:
                self.multi = json.loads(record['multi'])

class GiveawayEntry:
    __slots__ = ('guild_id', 'channel_id', 'message_id', 'title', 'host_id', 'donor_id', 'winners', 'required_roles', 'blacklisted_roles', 'bypass_roles', 'multi', 'duration', 'end_time', 'showentrantcount', 'active')

    def __init__(self, record: asyncpg.Record):
        self.guild_id: int = record.get('guild_id')
        self.channel_id: int = record.get('channel_id')
        self.message_id: int = record.get('message_id')
        self.title: str = record.get('title')
        self.host_id: int = record.get('host_id')
        self.donor_id: int = record.get('donor_id')
        self.winners: list = record.get('winners')
        self.required_roles: list = split_string_into_list(record.get('required_roles'), return_type=int)
        self.blacklisted_roles: list = split_string_into_list(record.get('blacklisted_roles'), return_type=int)
        self.bypass_roles: list = split_string_into_list(record.get('bypass_roles'), return_type=int)
        self.multi: dict = json.loads(record.get('multi'))
        self.duration: int = record.get('duration')
        self.end_time: int = record.get('end_time')
        self.showentrantcount: bool = record.get('showentrantcount')
        self.active: bool = record.get('active')


    def __repr__(self) -> str:
        return f"<GiveawayEntry title={self.title} channel_id={self.channel_id} message_id={self.message_id} host_id={self.host_id} winners={self.winners} required_roles={self.required_roles} blacklisted_roles={self.blacklisted_roles} multi={self.multi} duration={self.duration} end_time={self.end_time} active={self.active}>"