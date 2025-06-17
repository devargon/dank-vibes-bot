create table if not exists infections
(
    infectioncase serial,
    member_id     bigint                                                             not null
        constraint infections_pkey1
            primary key,
    guild_id      bigint,
    channel_id    bigint,
    message_id    bigint,
    infector      bigint,
    timeinfected  bigint
);