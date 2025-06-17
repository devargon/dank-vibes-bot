create table if not exists dumbfightlog
(
    invoker_id bigint,
    target_id  bigint,
    did_win    integer
);