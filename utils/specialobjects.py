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