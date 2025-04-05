create table if not exists old_userconfig
(
    user_id                bigint                not null
        constraint userconfig_pkey
            primary key,
    votereminder           bigint,
    dumbfight_result       boolean,
    dumbfight_rig_duration bigint,
    virus_immune           bigint,
    received_daily_potion  boolean,
    verification_reminded  boolean,
    watchlist_notify       integer,
    notify_about_logging   boolean default false,
    snipe_res_result       boolean,
    snipe_res_duration     bigint,
    rmtype                 bigint,
    bypass_ban             boolean default false not null
);
