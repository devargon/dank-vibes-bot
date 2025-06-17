create table if not exists payoutchannels
(
    channel_id     bigint not null
        primary key,
    ticket_user_id bigint,
    staff          bigint
);