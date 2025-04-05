create table if not exists changelog
(
    version_number serial,
    version_str    text,
    changelog      text
);