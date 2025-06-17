create table if not exists commandaccess
(
    member_id bigint,
    command   text,
    until     bigint
);