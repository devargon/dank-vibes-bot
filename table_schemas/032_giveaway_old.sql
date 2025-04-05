create table if not exists giveaway_old
(
    guild_id   bigint,
    channel_id bigint,
    message_id bigint,
    time       bigint,
    name       text,
    host_id    bigint,
    winners    integer,
    active     boolean not null
);