create table if not exists pollvotes
(
    poll_id integer,
    user_id bigint,
    choice  text
);