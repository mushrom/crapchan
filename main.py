#!/usr/bin/env python3

import sys
import time
import os
import sqlite3
import re

from flask import Flask
from flask import render_template
from flask import g
from flask import abort
from flask import request
from flask import Markup

app = Flask(__name__)

app.config.update(dict(
    DATABASE = os.path.join(app.root_path, 'lambdachan.db'),
    SECKRET_KEY = "dev key",
))

@app.route("/")
def index():
    return render_template('main_index.html',
            boards = get_boards())
    #return "Hello world!"

@app.route("/<board>/")
def board_index(board):
    row = get_board_id( board )

    i)f row == None:
    st
        abort(404)

    thread_ids = get_board_thread_ids( row[0] )
    post_ids   = [summarize_thread( get_thread_post_ids( x["thread_id"] ))
                      for x in thread_ids]

    boardsum = [{"thread" : x[0], "posts" : x[1][0], "omitted" : x[1][1]}
                    for x in zip( thread_ids, post_ids )]

    print( boardsum )

    return render_template('board_index.html',
            board            = board,
            boardsum         = boardsum,
            get_thread_by_id = get_thread_by_id,
            get_post_by_id   = get_post_by_id,
            time             = time )

@app.route("/thread/<int:thread_id>")
def board_thread(thread_id):
    post_ids = get_thread_post_ids( thread_id )

    return render_template('thread.html',
            thread         = get_thread_by_id( thread_id ),
            post_ids       = post_ids,
            board          = "test",
            get_post_by_id = get_post_by_id,
            time           = time )

    #return "showing thread %s in board /%s/" % (thread_id, "asdf")

@app.route("/post-thread/<board>", methods=["POST"])
def create_new_thread(board):
    if request.method == 'POST':
        print( "got subject:<br/>" + request.form["subject"] + "<br />got content:<br />" + request.form["content"] + "<br />" )

        board_id = get_board_id( board )

        if board_id == None:
            abort(404)
        else:
            board_id = board_id[0]

        subject = request.form["subject"]
        if subject == "":
            subject = "<no subject>"

        db = get_db()

        db.execute("insert into threads(subject) values (?)",
                    (subject,))

        thread_id = get_max_thread_number()

        db.execute("""
            insert into threads_in_boards(
                thread_id,
                board_id,
                last_updated
            ) values (?,?,?)
        """, (thread_id, board_id, time.time()))

        add_post(thread_id, "Anonymous", request.form["content"])
        db.commit()

        return """
            <!doctype html>
            <html>
                <head><title>Success!</title></head>
                <body>
                    <h3>Thread has been made successfully.</h3>
                    <a href='/""" + board + """/'>return</a>
                </body>
            </html>
        """

    else:
        return 'huh?'

@app.route("/reply/<int:thread_id>", methods=["POST"])
def reply_to_thread(thread_id):
    if request.method == "POST":
        add_post(thread_id, request.form["name"], request.form["content"])
        update_thread_time(thread_id)

        return """
            <!doctype html>
            <html>
                <head><title>Success!</title></head>
                <body>
                    <h3>Post has been made successfully.</h3>
                    <a href='/thread/""" + str(thread_id) + """'>return</a>
                </body>
            </html>
        """

    else:
        return "huh?"

@app.route("/create-board", methods=["POST"])
def create_board():
    if request.method == 'POST':
        thing = get_board_id(request.form["name"])

        print(thing)
        if thing == None:
            add_board( request.form["name"], request.form["description"])
            return """
                <!doctype html>
                <html>
                    <head><title>Success!</title></head>
                    <body>
                        <h3>Board was created successfully.</h3>
                        <a href='/'>return</a>
                    </body>
                </html>
            """

        else:
            return "board already exists!"

    else:
        return 'huh?'

@app.route("/admin")
def admin():
    return render_template('admin.html',
            flagged_posts = get_post_by_flagged())

@app.route("/flag-post/<int:post_id>", methods=["POST"])
def flag_post(post_id):
    db = get_db()
    db.execute("update "+post_id+" set flagged=1")

    return """
        <!doctype html>
        <html>
            <head><title>Success!</title></head>
            <body>
                <font color="red"><h3>Post has been flagged for moderation.</h3></font>
                <a href='/'>return</a>
            </body>
        </html>
    """

def get_thread_by_id( thread_id ):
    db = get_db()
    row = db.execute("select * from threads where id=? and hidden = 0", (thread_id,))
    return row.fetchone()

def get_post_by_id( post_id ):
    db = get_db()
    row = db.execute("select * from posts where id=? and hidden = 0", (post_id))
    return row.fetchone()

def get_post_by_flagged(post_id):
    db = get_db()
    db.execute("select * from posts where flagged=1", (post_id))

def get_board_thread_ids( board_id ):
    db = get_db()

    row = db.execute("""
        select thread_id from threads_in_boards
            where board_id=?
            order by last_updated desc
    """, (board_id,))

    return row.fetchall()

def get_boards():
    db = get_db()
    row = db.execute("select * from boards")
    return row.fetchall()

def get_board_id( name ):
    db = get_db()
    row = db.execute("select id from boards where name=?", (name,))
    return row.fetchone()

def get_thread_post_ids( thread_id ):
    db = get_db()

    row = db.execute("""
        select post_id from posts_in_threads
            where thread_id=?
            order by post_id asc
    """, (thread_id,))

    return row.fetchall()

def get_max_post_number( ):
    db = get_db()

    row = db.execute( "select max(id) from posts where hidden = 0" )
    row = row.fetchone()

    if row != None:
        return row[0]
    else:
        return 1;

def get_max_board_id( ):
    db = get_db()

    row = db.execute( "select max(id) from boards" )
    row = row.fetchone()

    if row != None:
        return row[0]
    else:
        return 1;

def get_max_thread_number( ):
    db = get_db()

    row = db.execute( "select max(id) from threads" )
    row = row.fetchone()

    if row != None:
        return row[0]
    else:
        return 1;

def summarize_thread( post_ids, sum_size=4 ):
    if len(post_ids) > sum_size:
        omitted = len(post_ids) - sum_size

        print( "ommited " + str(omitted) + " posts")

        return ([post_ids[0]] + post_ids[-sum_size + 1:], omitted)

    else:
        return (post_ids, 0)

def add_post(thread_id, name, content):
    db = get_db()

    escaped = str(Markup.escape(content))
    escaped = re.sub( r'&gt;&gt;([0-9]*)',
                      r'<a href="#p\1">&gt;&gt;\1</a>',
                      escaped );

    escaped = re.sub( r'^&gt;(.*)$',
                     r'<span class="thread_post_quote">&gt;\1</span>',
                     escaped,
                     0,
                     re.MULTILINE )

    escaped = escaped.replace( "\n", "<br />" )

    print( "have " + escaped )
    #print( "thing: " + foo )

    db.execute("""
        insert into posts(name, content, post_time, flagged, hidden)
            values (?,?,?,0,0)
    """, (name, escaped, time.time()))

    post_id = get_max_post_number()

    db.execute("insert into posts_in_threads(post_id, thread_id) values (?,?)",
                (post_id, thread_id))

    db.commit()

    return post_id

def add_board(name, description):
    db = get_db()

    db.execute("""
        insert into boards(name, description)
            values (?,?)
    """, (name, description))

    db.commit()

    return get_max_board_id()

def update_thread_time(thread_id):
    db = get_db()

    db.execute("""
        update threads_in_boards
            set last_updated=?
            where thread_id=?
    """, (time.time(), thread_id))

    db.commit()

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

@app.cli.command('initdb')
def setup_db():
    db = get_db()

    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())

    db.commit()

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()

    return g.sqlite_db

if __name__ == "__main__":
    if not os.path.exists(app.config['DATABASE']):
        print( "Database not found, setting up a fresh one..." )
        setup_db()

    app.run()
