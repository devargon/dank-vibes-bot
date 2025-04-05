create table if not exists giveawayconfig
(
    guild_id          bigint not null,
    channel_id        bigint not null
        primary key,
    bypass_roles      text,
    blacklisted_roles text,
    multi             jsonb
);