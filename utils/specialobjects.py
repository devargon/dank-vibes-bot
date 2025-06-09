from datetime import datetime, timezone
from typing import Any, Union, Optional, Literal

import aiohttp
import discord


class Reminder:
    __slots__ = ('time', 'name', 'channel', 'guild', 'message', 'id', 'user', 'created_time', 'repeat', 'interval')

    def __init__(self, *, record):
        self.id = record.get('id')
        self.user = record.get('user_id')
        self.guild = record.get('guild_id')
        self.channel = record.get('channel_id')
        self.message = record.get('message_id')
        self.created_time = record.get('created_time')
        self.time = record.get('time')
        self.name = record.get('name')
        self.repeat = record.get('repeat')
        self.interval = record.get('interval')

class _MissingSentinel:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return "..."


class ContestSubmission:
    __slots__ = ('contest_id', 'entry_id', 'submitter_id', 'media_link', 'second_media_link', 'approve_id', 'msg_id', 'approved')

    def __init__(self, record):
        self.contest_id: int = record.get('contest_id')
        self.entry_id: int = record.get('entry_id')
        self.submitter_id: int = record.get('submitter_id')
        self.media_link: str = record.get('media_link')
        self.second_media_link: str = record.get('second_media_link')
        self.approve_id: Union[int, None] = record.get('approve_id')
        self.msg_id: Union[int, None] = record.get('msg_id')
        self.approved: bool = record.get('approved')

    def __repr__(self):
        return f"<ContestSubmission contest_id={self.contest_id} entry_id={self.entry_id} submitter_id={self.submitter_id} media_link={self.media_link} second_media_link={self.second_media_link} approve_id={self.approve_id} msg_id={self.msg_id} approved={self.approved}>"


class Contest:
    __slots__ = ('contest_id', 'guild_id', 'contest_starter_id', 'contest_channel_id', 'name', 'created', 'active', 'voting')

    def __init__(self, record):
        self.contest_id: int = record.get('contest_id')
        self.guild_id: int = record.get('guild_id')
        self.contest_starter_id: int = record.get('contest_starter_id')
        self.contest_channel_id: int = record.get("contest_channel_id")
        self.name: str = record.get('name')
        self.created: int = record.get('created')
        self.active: bool = record.get('active')
        self.voting: bool = record.get('voting')

    def __repr__(self) -> str:
        return f"<ContestSubmission contest_id={self.contest_id} guild_id={self.guild_id} contest_starter_id={self.contest_starter_id} contest_channel_id={self.contest_channel_id} name={self.name} created={self.created} active={self.active} voting={self.voting}>"

class DankItem:
    __slots__ = ('name', 'plural_name', 'idcode', 'type', 'image_url', 'trade_value', 'last_updated', 'overwrite', 'celeb_donation', 'celeb_overwrite_value')

    def __init__(self, record):
        self.name: str = record.get('name')
        self.plural_name: str = record.get('plural_name')
        self.idcode: str = record.get('idcode')
        self.type: str = record.get('type')
        self.image_url: str = record.get('image_url')
        self.trade_value: int = record.get('trade_value')
        self.last_updated: int = record.get('last_updated')
        self.overwrite: bool = record.get('overwrite')
        self.celeb_donation: bool = record.get('celeb_donation')
        self.celeb_overwrite_value: int = record.get('celeb_overwrite_value')

    def __repr__(self) -> str:
        attributes = ["DankItem"]
        for attr in dir(self):
            if not attr.startswith('__'):
                attributes.append(f"{attr}={self.__getattribute__(attr)}")
        repr_string = " ".join(attributes)
        repr_string = "<" + repr_string + ">"
        return repr_string


class ServerConfiguration:
    __slots__ = ('guild_id', 'owodailylb', 'verification', 'censor', 'owoweeklylb', 'votelb', 'timeoutlog', 'pls_ar', 'mrob_ar', 'statusroleenabled', 'statusroleid', 'statustext', 'statusmatchtype', 'autoban_duration', 'auto_decancer', 'log_channel', 'modlog_channel', 'mute_lem', 'serverpool_donation_log', 'enable_amari_transfer')

    def __init__(self, record):
        self.guild_id: int = record.get('guild_id')
        self.owodailylb: bool = record.get('owodailylb')
        self.verification: bool = record.get('verification')
        self.censor: bool = record.get('censor')
        self.owoweeklylb: bool = record.get('owoweeklylb')
        self.votelb: bool = record.get('votelb')
        self.timeoutlog: bool = record.get('timeoutlog')
        self.pls_ar: bool = record.get('pls_ar')
        self.mrob_ar: bool = record.get('mrob_ar')
        self.statusroleenabled: bool = record.get('statusrole')
        self.statusroleid: int = record.get('statusroleid')
        self.statustext: str = record.get('statustext')
        self.statusmatchtype: str = record.get('statusmatchtype')
        self.autoban_duration: int = record.get('autoban_duration')
        self.auto_decancer: bool = record.get('auto_decancer')
        self.log_channel: int = record.get('log_channel')
        self.modlog_channel: int = record.get('modlog_channel')
        self.mute_lem: bool = record.get('mute_lem')
        self.serverpool_donation_log: bool = record.get('serverpool_donation_log')
        self.enable_amari_transfer: bool = record.get('enable_amari_transfer')

    def __repr__(self) -> str:
        return f"<ServerConfiguration guild_id={self.guild_id} owodailylb={self.owodailylb} verification={self.verification} censor={self.censor} owoweeklylb={self.owoweeklylb} votelb={self.votelb} timeoutlog={self.timeoutlog} pls_ar={self.pls_ar} mrob_ar={self.mrob_ar} statusroleenabled={self.statusroleenabled} statusroleid={self.statusroleid} statustext={self.statustext} statusmatchtype={self.statusmatchtype} autoban_duration={self.autoban_duration} auto_decancer={self.auto_decancer} log_channel={self.log_channel} modlog_channel={self.modlog_channel} mute_log={self.mute_log} serverpool_donation_log={self.serverpool_donation_log} enable_amari_transfer={self.enable_amari_transfer}>"

    async def update(self, client):
        a = await client.db.execute("UPDATE serverconfig SET owodailylb=$1, verification=$2, censor=$3, owoweeklylb=$4, votelb=$5, timeoutlog=$6, pls_ar=$7, mrob_ar=$8, statusrole=$9, statusroleid=$10, statustext=$11, statusmatchtype=$12, autoban_duration = $13, auto_decancer = $14, log_channel = $15, modlog_channel = $16, mute_lem = $17, serverpool_donation_log = $18, enable_amari_transfer = $19 WHERE guild_id = $20",
                                self.owodailylb, self.verification, self.censor, self.owoweeklylb, self.votelb, self.timeoutlog, self.pls_ar, self.mrob_ar, self.statusroleenabled, self.statusroleid, self.statustext, self.statusmatchtype, self.autoban_duration, self.auto_decancer, self.log_channel, self.modlog_channel, self.mute_lem, self.serverpool_donation_log, self.enable_amari_transfer, self.guild_id)
        client.serverconfig[self.guild_id] = self

class UserInfo:
    __slots__ = ('user_id', 'notify_about_logging', 'bypass_ban', 'heists', 'heistamt', 'timezone')
    def __init__(self, record):
        self.user_id: int = record.get('user_id')
        self.notify_about_logging: bool = record.get('notify_about_logging')
        self.bypass_ban: bool = record.get('bypass_ban')
        self.heists: int = record.get('heists')
        self.heistamt: int = record.get('heistamt')
        self.timezone: str = record.get("timezone")

    def __repr__(self) -> str:
        return f"<UserInfo user_id={self.user_id} notify_about_logging={self.notify_about_logging} bypass_ban={self.bypass_ban} heists={self.heists} heistamt={self.heistamt}> timezone={self.timezone}"

    async def update(self, client):
        a = await client.db.execute("UPDATE userinfo SET notify_about_logging=$1, bypass_ban=$2, heists=$3, heistamt=$4 WHERE user_id = $5", self.notify_about_logging, self.bypass_ban, self.heists, self.heistamt, self.user_id)

class PrivateChannel:
    __slots__ = ('owner', 'channel', 'last_used', 'add_members', 'remove_members', 'edit_name', 'edit_topic', 'ignore_member_limit', 'restriction_reason')

    def __init__(self, owner, channel, record):
        self.owner: discord.Member = owner
        self.channel: discord.TextChannel = channel
        self.last_used: int = record.get('last_used')
        self.add_members: bool = record.get('add_members')
        self.remove_members: bool = record.get('remove_members')
        self.edit_name: bool = record.get('edit_name')
        self.edit_topic: bool = record.get('edit_topic')
        self.ignore_member_limit: bool = record.get('ignore_member_limit')
        self.restriction_reason: Union[str, None] = record.get('restriction_reason')

    async def update(self, client):
        a = await client.db.execute("UPDATE channels SET last_used = $1, add_members = $2, remove_members = $3, edit_name = $4, edit_topic = $5, ignore_member_limit = $6, restriction_reason = $7 WHERE channel_id = $8",
                                    self.last_used, self.add_members, self.remove_members, self.edit_name,
                                    self.edit_topic, self.ignore_member_limit, self.restriction_reason, self.channel.id)


def make_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


from typing import Optional
from datetime import datetime
import asyncpg


class AmariImportTask:
    def __init__(
            self,
            record: Optional[asyncpg.Record] = None,
            *,
            id: Optional[int] = None,
            user_id: Optional[int] = None,
            status: Optional[str] = None,
            created_at: Optional[datetime] = None,
            enqueued_at: Optional[datetime] = None,
            updated_at: Optional[datetime] = None,
            stopped_at: Optional[datetime] = None,
            ticket_guild_id: Optional[int] = None,
            ticket_channel_id: Optional[int] = None,
            ticket_message_id: Optional[int] = None,
            notified_near_front: Optional[bool] = None,
            error_message: Optional[str] = None,
            ticket_message: Optional[str] = None,
            amari_xp_to_add: Optional[int] = None,
            expected_amari_level: Optional[int] = None,
            expected_total_amari_xp: Optional[int] = None,
            position: int = -1,
    ):
        if record:
            self.id = record['id']
            self.user_id = record['user_id']
            self.status = record['status']
            self.created_at = make_utc(record['created_at'])
            self.enqueued_at = make_utc(record.get('enqueued_at'))
            self.updated_at = make_utc(record.get('updated_at'))
            self.stopped_at = make_utc(record.get('stopped_at'))
            self.ticket_guild_id = record['ticket_guild_id']
            self.ticket_channel_id = record['ticket_channel_id']
            self.ticket_message_id = record['ticket_message_id']
            self.notified_near_front = record['notified_near_front']
            self.error_message = record.get('error_message')
            self.ticket_message = record.get('ticket_message')
            self.amari_xp_to_add = record['amari_xp_to_add']
            self.expected_amari_level = record['expected_amari_level']
            self.expected_total_amari_xp = record['expected_total_amari_xp']
            self.position = record.get('position', -1)
        else:
            self.id = id
            self.user_id = user_id
            self.status = status
            self.created_at = created_at
            self.enqueued_at = enqueued_at
            self.updated_at = updated_at
            self.stopped_at = stopped_at
            self.ticket_guild_id = ticket_guild_id
            self.ticket_channel_id = ticket_channel_id
            self.ticket_message_id = ticket_message_id
            self.notified_near_front = notified_near_front
            self.error_message = error_message
            self.ticket_message = ticket_message
            self.amari_xp_to_add = amari_xp_to_add
            self.expected_amari_level = expected_amari_level
            self.expected_total_amari_xp = expected_total_amari_xp
            self.position = position

    def __repr__(self):
        return f"<AmariImportTaskQueue id={self.id} status={self.status} user_id={self.user_id} position={self.position}>"

    async def update(self, client):
        def enforce_utc_aware(dt):
            if dt is None:
                return None
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        # Enforce UTC awareness on datetime fields
        self.enqueued_at = enforce_utc_aware(self.enqueued_at)
        self.updated_at = enforce_utc_aware(self.updated_at)
        self.stopped_at = enforce_utc_aware(self.stopped_at)

        await client.db.execute("""
            UPDATE amari_import_task_queue SET
                status = $1,
                enqueued_at = $2,
                updated_at = $3,
                stopped_at = $4,
                ticket_guild_id = $5,
                ticket_channel_id = $6,
                ticket_message_id = $7,
                notified_near_front = $8,
                error_message = $9,
                ticket_message = $10,
                amari_xp_to_add = $11,
                expected_amari_level = $12,
                expected_total_amari_xp = $13
            WHERE id = $14
        """, self.status, self.enqueued_at, self.updated_at, self.stopped_at, self.ticket_guild_id,
                                self.ticket_channel_id, self.ticket_message_id, self.notified_near_front,
                                self.error_message, self.ticket_message, self.amari_xp_to_add,
                                self.expected_amari_level, self.expected_total_amari_xp, self.id)

class AmariImportTaskLog:
    def __init__(
        self,
        record: Optional[asyncpg.Record] = None,
        *,
        id: Optional[int] = None,
        task_id: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        status_before: Optional[str] = None,
        status_after: Optional[str] = None,
        event: Optional[str] = None,
        event_user_id: Optional[int] = None,
        details: Optional[str] = None,
    ):
        if record:
            self.id = record['id']
            self.task_id = record['task_id']
            self.timestamp = make_utc(record['timestamp'])
            self.status_before = record['status_before']
            self.status_after = record['status_after']
            self.event = record['event']
            self.event_user_id = record['event_user_id']
            self.details = record.get('details')
        else:
            self.id = id
            self.task_id = task_id
            self.timestamp = timestamp
            self.status_before = status_before
            self.status_after = status_after
            self.event = event
            self.event_user_id = event_user_id
            self.details = details

    def __repr__(self):
        return f"<AmariImportTaskLogs id={self.id} task_id={self.task_id} event={self.event}>"

    async def update(self, client):
        await client.db.execute("""
            UPDATE amari_import_task_logs SET
                task_id = $1,
                timestamp = $2,
                status_before = $3,
                status_after = $4,
                event = $5,
                event_user_id = $6,
                details = $7
            WHERE id = $8
        """, self.task_id, self.timestamp, self.status_before, self.status_after,
             self.event, self.event_user_id, self.details, self.id)


class AmariImportWorker:
    def __init__(
        self,
        record: Optional[asyncpg.Record] = None,
        *,
        id: Optional[int] = None,
        host: Optional[str] = None,
        token: Optional[str] = None,
        created_at: Optional[datetime] = None,
        worker_user_id: Optional[int] = None,
        creator_user_id: Optional[int] = None,
    ):
        if record:
            self.id = record['id']
            self.host = record['host']
            self.token = record['token']
            self.created_at = make_utc(record['created_at'])
            self.worker_user_id = record['worker_user_id']
            self.creator_user_id = record['creator_user_id']
        else:
            self.id = id
            self.host = host
            self.token = token
            self.created_at = created_at
            self.worker_user_id = worker_user_id
            self.creator_user_id = creator_user_id

    def __repr__(self):
        return f"<AmariImportWorkers id={self.id} host={self.host}>"

    async def update(self, client):
        await client.db.execute("""
            UPDATE amari_import_workers SET
                host = $1,
                token = $2,
                worker_user_id = $3,
                creator_user_id = $4
            WHERE id = $5
        """, self.host, self.token, self.worker_user_id, self.creator_user_id, self.id)

    async def fetch_status(self, aiohttp_client: aiohttp.ClientSession):
        response = await self.make_request(aiohttp_client, "status", timeout=5.0)
        return response

    async def give_level(self, aiohttp_client: aiohttp.ClientSession, guild_id: int, channel_id: int, user_id: int, level: int):
        data = {
            "user_id": str(user_id),
            "level": level
        }
        response = await self.make_request(aiohttp_client, f"givelevel/{guild_id}/{channel_id}", method="POST", data=data, timeout=30.0)
        return response

    async def modify_exp(self, aiohttp_client: aiohttp.ClientSession, guild_id: int, channel_id: int, user_id: int, action: Literal['add', 'remove'], exp: int):
        data = {
            "user_id": str(user_id),
            "action": action,
            "exp": exp
        }
        response = await self.make_request(aiohttp_client, f"modifyexp/{guild_id}/{channel_id}", method="POST", data=data, timeout=30.0)
        return response

    async def make_request(self, aiohttp_client: aiohttp.ClientSession, endpoint: str, method: str = 'GET', data: Optional[dict] = None, timeout=5.0):
        host = self.host.rstrip("/")
        endpoint = endpoint.lstrip("/")
        url = f"{host}/{endpoint}"

        headers = {'Authorization': f"Bearer {self.token}"}

        if method == "POST":
            print(f"[AmariImportWorker] POST {url} with data: {data}")
            async with aiohttp_client.post(url, json=data, headers=headers) as response:
                if response.status == 204:
                    return True  # or {} if you prefer an empty dict
                elif response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        else:
            print(f"[AmariImportWorker] GET {url}")
            async with aiohttp_client.get(url, headers=headers) as response:
                if response.status == 204:
                    return True  # or {} if you prefer an empty dict
                elif response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()  # Raises an exception for 4xx/5xx errors


MISSING: Any = _MissingSentinel()


class AwaitingAmariData:
    pass


class NoAmariData:
    pass