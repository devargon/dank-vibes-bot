create table if not exists contest_submissions
(
    contest_id        integer not null,
    entry_id          integer,
    submitter_id      bigint  not null,
    media_link        text    not null,
    second_media_link text,
    approve_id        bigint,
    msg_id            bigint,
    approved          boolean default false
);