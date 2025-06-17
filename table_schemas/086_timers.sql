create table if not exists timers
(
    guild_id   bigint,
    channel_id bigint,
    message_id bigint,
    user_id    bigint,
    time       bigint,
    title      text
);