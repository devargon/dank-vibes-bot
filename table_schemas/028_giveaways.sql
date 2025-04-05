create table if not exists giveaways
(
    guild_id          bigint  not null,
    channel_id        bigint  not null,
    message_id        bigint  not null,
    title             text    not null,
    host_id           bigint  not null,
    donor_id          bigint,
    winners           integer not null,
    required_roles    text,
    blacklisted_roles text,
    bypass_roles      text,
    multi             jsonb,
    amari_level       integer default 0,
    amari_weekly_xp   integer default 0,
    duration          integer not null,
    end_time          bigint  not null,
    showentrantcount  boolean default true,
    active            boolean default true,
    ended_message_id  bigint
);