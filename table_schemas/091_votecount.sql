create table if not exists votecount
(
    member_id bigint not null
        constraint votecount_pkey1
            primary key,
    count     integer
);
