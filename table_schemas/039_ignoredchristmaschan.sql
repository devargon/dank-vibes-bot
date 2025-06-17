create table if not exists ignoredchristmaschan
(
    guild_id   bigint,
    channel_id bigint not null
        primary key
);