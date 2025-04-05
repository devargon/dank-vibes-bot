create table if not exists userinfo
(
    user_id              bigint            not null
        constraint userinfo_user_id_pkey
            primary key,
    notify_about_logging boolean default false,
    bypass_ban           boolean default false,
    heists               integer default 0 not null,
    heistamt             bigint  default 0 not null,
    timezone             text
);