create table if not exists usercleanup
(
    guild_id   bigint,
    target_id  bigint,
    channel_id bigint,
    message    text
);