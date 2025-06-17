create table if not exists voters
(
    member_id         bigint                not null
        constraint votecount_pkey
            primary key,
    count             integer default 0     not null,
    rmtype            integer default 1     not null,
    rmtime            bigint,
    topgg_deprecation boolean default false not null
);
