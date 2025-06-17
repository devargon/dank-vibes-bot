create table if not exists stickymessages
(
    guild_id   bigint,
    channel_id bigint not null
        primary key,
    message_id bigint,
    type       integer,
    message    text
);