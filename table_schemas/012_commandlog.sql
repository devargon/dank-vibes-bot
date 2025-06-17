create table if not exists commandlog
(
    guild_id               bigint,
    channel_id             bigint,
    message_id             bigint,
    user_id                bigint,
    command                text,
    message                text,
    time                   bigint,
    is_application_command boolean
);