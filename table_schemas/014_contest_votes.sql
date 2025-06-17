create table if not exists contest_votes
(
    contest_id integer not null,
    entry_id   integer,
    user_id    bigint  not null
);