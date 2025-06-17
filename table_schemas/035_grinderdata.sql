create table if not exists grinderdata
(
    user_id        bigint           not null
        primary key,
    today          bigint default 0 not null,
    past_week      bigint default 0 not null,
    last_week      bigint default 0 not null,
    past_month     bigint default 0 not null,
    all_time       bigint default 0 not null,
    last_dono_time bigint,
    last_dono_msg  text,
    advance_amt    bigint
);