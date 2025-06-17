create table if not exists polls
(
    poll_id            serial,
    guild_id           bigint,
    channel_id         bigint,
    invoked_message_id bigint,
    message_id         bigint,
    creator_id         bigint,
    poll_name          text,
    choices            text,
    created            bigint,
    anonymous          boolean default false
);