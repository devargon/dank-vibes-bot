create table if not exists channels
(
    guild_id            bigint,
    channel_id          bigint                not null
        primary key,
    owner_id            bigint,
    active              boolean default false,
    last_used           bigint  default 0     not null,
    add_members         boolean default true  not null,
    remove_members      boolean default true  not null,
    edit_topic          boolean default true  not null,
    edit_name           boolean default true  not null,
    restriction_reason  text,
    ignore_member_limit boolean default false not null
);