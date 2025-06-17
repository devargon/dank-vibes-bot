create table if not exists roleremove
(
    member_id bigint not null
        primary key,
    rmtime    bigint,
    roletime  bigint
);