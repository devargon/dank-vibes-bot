create table if not exists owocount
(
    member_id    bigint not null
        primary key,
    daily_count  integer,
    weekly_count integer,
    total_count  integer,
    yesterday    integer,
    last_week    integer
);
