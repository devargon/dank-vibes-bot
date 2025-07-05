create table if not exists messagecount
(
    guild_id bigint not null,
    user_id      bigint not null,
    mcount bigint not null default 0
);