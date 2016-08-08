drop table if exists posts;
drop table if exists threads;
drop table if exists posts_in_threads;
drop table if exists threads_in_boards;
drop table if exists boards;

create table posts (
    id integer primary key autoincrement,
    post_time integer,
    name text not null,
    content text not null
);

create table threads (
    id integer primary key autoincrement,
    subject text not null
);

create table posts_in_threads (
    post_id   integer,
    thread_id integer
);

create table threads_in_boards (
    thread_id     integer,
    board_id      integer,
    last_updated  integer
);

create table boards (
    id integer primary key autoincrement,
    name text not null
);

insert into boards(name) values ('prog');
insert into boards(name) values ('tech');
insert into boards(name) values ('lisp');
