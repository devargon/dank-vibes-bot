create table if not exists tempweekly
(
    member_id bigint not null
        primary key,
    yesterday integer,
    last_week integer
);