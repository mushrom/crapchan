drop table if exists posts;
drop table if exists threads;
drop table if exists posts_in_threads;
drop table if exists threads_in_boards;
drop table if exists boards;

create table posts (
    id           integer primary key autoincrement,
    thread       integer,
    post_time    integer,
    name text    not null,
    content text not null,
    flagged      boolean,
    hidden       boolean
);

create table threads (
    id           integer primary key autoincrement,
    board        integer,
    last_updated integer,
    subject      text not null,
    flagged      boolean,
    hidden       boolean
);

create table boards (
    id          integer primary key autoincrement,
    name        text not null,
    description text not null
);
