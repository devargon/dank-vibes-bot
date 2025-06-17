create table if not exists ignoredchristmascat
(
    guild_id    bigint,
    category_id bigint not null
        primary key
);