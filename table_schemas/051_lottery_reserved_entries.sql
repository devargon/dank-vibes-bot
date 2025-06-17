create table if not exists lottery_reserved_entries
(
    lottery_id     integer,
    lottery_user   bigint,
    lottery_number integer
);