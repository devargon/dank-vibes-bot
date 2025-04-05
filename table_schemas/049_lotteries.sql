create table if not exists lotteries
(
    lottery_id    serial,
    lottery_type  text,
    guild_id      bigint               not null,
    starter_id    bigint               not null,
    lottery_entry text                 not null,
    active        boolean default true not null
);