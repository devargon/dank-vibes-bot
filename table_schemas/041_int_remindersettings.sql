create table if not exists int_remindersettings
(
    member_id bigint not null
        constraint remindersettings_pkey
            primary key,
    method    integer,
    daily     bigint,
    lottery   bigint,
    work      bigint,
    lifesaver bigint,
    redeem    integer,
    weekly    integer,
    monthly   integer,
    hunt      integer,
    fish      integer,
    dig       integer,
    highlow   integer,
    snakeeyes integer,
    search    integer,
    crime     integer,
    beg       integer,
    dailybox  integer,
    horseshoe integer,
    pizza     integer,
    drop      integer,
    stream    integer,
    postmeme  integer,
    marriage  integer,
    pet       integer,
    m_partner bigint,
    adventure integer
);