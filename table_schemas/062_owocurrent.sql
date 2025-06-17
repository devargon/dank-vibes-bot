create table if not exists owocurrent
(
    member_id    bigint not null
        primary key,
    daily_count  integer,
    weekly_count integer,
    total_count  integer
);