create table if not exists prefixes
(
    guild_id bigint not null
        primary key,
    prefix   text
);