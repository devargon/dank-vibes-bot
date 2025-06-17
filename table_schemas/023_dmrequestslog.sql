create table if not exists dmrequestslog
(
    id          bigint,
    member_id   bigint,
    target_id   bigint,
    approver_id bigint,
    dmcontent   text,
    status      integer
);