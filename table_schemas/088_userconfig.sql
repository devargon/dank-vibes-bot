create table if not exists userconfig
(
    user_id                bigint                not null
        constraint userconfig_user_id_pkey
            primary key,
    votereminder           bigint,
    dumbfight_result       boolean,
    dumbfight_rig_duration bigint,
    snipe_res_result       boolean,
    snipe_res_duration     bigint,
    received_daily_potion  boolean default false not null,
    watchlist_notify       integer default 0     not null
);