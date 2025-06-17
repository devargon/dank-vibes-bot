create table if not exists contests
(
    contest_id         serial,
    guild_id           bigint not null,
    contest_starter_id bigint not null,
    contest_channel_id bigint not null,
    name               text,
    created            bigint,
    active             boolean default true,
    voting             boolean default false
);