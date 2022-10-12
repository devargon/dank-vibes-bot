from typing import Any, Union


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
    __slots__ = ('guild_id', 'owodailylb', 'verification', 'censor', 'owoweeklylb', 'votelb', 'timeoutlog', 'pls_ar', 'mrob_ar', 'statusroleenabled', 'statusroleid', 'statustext', 'statusmatchtype', 'autoban_duration', 'auto_decancer', 'log_channel', 'modlog_channel', 'mute_lem', 'serverpool_donation_log')

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

    def __repr__(self) -> str:
        return f"<ServerConfiguration guild_id={self.guild_id} owodailylb={self.owodailylb} verification={self.verification} censor={self.censor} owoweeklylb={self.owoweeklylb} votelb={self.votelb} timeoutlog={self.timeoutlog} pls_ar={self.pls_ar} mrob_ar={self.mrob_ar} statusroleenabled={self.statusroleenabled} statusroleid={self.statusroleid} statustext={self.statustext} statusmatchtype={self.statusmatchtype} autoban_duration={self.autoban_duration} auto_decancer={self.auto_decancer} log_channel={self.log_channel} modlog_channel={self.modlog_channel} mute_log={self.mute_log} serverpool_donation_log={self.serverpool_donation_log}>"

    async def update(self, client):
        a = await client.db.execute("UPDATE serverconfig SET owodailylb=$1, verification=$2, censor=$3, owoweeklylb=$4, votelb=$5, timeoutlog=$6, pls_ar=$7, mrob_ar=$8, statusrole=$9, statusroleid=$10, statustext=$11, statusmatchtype=$12, autoban_duration = $13, auto_decancer = $14, log_channel = $15, modlog_channel = $16, mute_lem = $17, serverpool_donation_log = $18 WHERE guild_id = $19",
                                self.owodailylb, self.verification, self.censor, self.owoweeklylb, self.votelb, self.timeoutlog, self.pls_ar, self.mrob_ar, self.statusroleenabled, self.statusroleid, self.statustext, self.statusmatchtype, self.autoban_duration, self.auto_decancer, self.log_channel, self.modlog_channel, self.mute_lem, self.serverpool_donation_log, self.guild_id)
        client.serverconfig[self.guild_id] = self

class UserInfo:
    __slots__ = ('user_id', 'notify_about_logging', 'bypass_ban', 'heists', 'heistamt')
    def __init__(self, record):
        self.user_id: int = record.get('user_id')
        self.notify_about_logging: bool = record.get('notify_about_logging')
        self.bypass_ban: bool = record.get('bypass_ban')
        self.heists: int = record.get('heists')
        self.heistamt: int = record.get('heistamt')

    def __repr__(self) -> str:
        return f"<UserInfo user_id={self.user_id} notify_about_logging={self.notify_about_logging} bypass_ban={self.bypass_ban} heists={self.heists} heistamt={self.heistamt}>"

    async def update(self, client):
        a = await client.db.execute("UPDATE userinfo SET notify_about_logging=$1, bypass_ban=$2, heists=$3, heistamt=$4 WHERE user_id = $5", self.notify_about_logging, self.bypass_ban, self.heists, self.heistamt, self.user_id)


MISSING: Any = _MissingSentinel()


class AwaitingAmariData:
    pass


class NoAmariData:
    pass