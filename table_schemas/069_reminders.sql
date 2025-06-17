create table if not exists reminders
(
    id           serial,
    user_id      bigint,
    guild_id     bigint,
    channel_id   bigint,
    message_id   bigint,
    name         text,
    time         bigint,
    created_time bigint,
    repeat       boolean default false not null,
    interval     integer
);