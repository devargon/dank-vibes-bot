create table if not exists serverconfig
(
    guild_id                bigint                              not null
        primary key,
    owodailylb              boolean default false               not null,
    verification            boolean default true                not null,
    censor                  boolean default false               not null,
    owoweeklylb             boolean default true                not null,
    votelb                  boolean default true                not null,
    timeoutlog              boolean default false               not null,
    statusrole              boolean default false               not null,
    statusroleid            bigint  default 0                   not null,
    statustext              text    default 'lorem ipsum'::text not null,
    statusmatchtype         text    default 'Strict'::text      not null,
    pls_ar                  boolean default false               not null,
    mrob_ar                 boolean default false               not null,
    auto_decancer           boolean default false               not null,
    autoban_duration        integer default 0                   not null,
    log_channel             bigint  default 0                   not null,
    modlog_channel          bigint  default 0                   not null,
    mute_lem                boolean default false,
    serverpool_donation_log boolean default false
);