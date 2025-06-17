create table if not exists rmpreference
(
    member_id bigint not null
        primary key,
    rmtype    integer
);