create table if not exists joinmessages
(
    guild_id      bigint not null
        primary key,
    channel_id    bigint,
    plain_text    text,
    embed_details text,
    delete_after  integer
);