create table if not exists dankreminders
(
    member_id    bigint,
    remindertype integer,
    channel_id   bigint,
    guild_id     bigint,
    time         bigint
);