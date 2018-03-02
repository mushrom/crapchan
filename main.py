#!/usr/bin/env python3

import sys
import time
import os
import sqlite3
import re
import yaml

from flask import Flask
from flask import render_template
from flask import g
from flask import abort
from flask import request
from flask import redirect
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

    if row == None:
        abort(404)

    threads = get_board_threads( row[0] )
    posts   = [summarize_thread( get_thread_posts(x["id"]))
                      for x in threads]

    boardsum = [{"thread" : x[0], "posts" : x[1][0], "omitted" : x[1][1]}
                    for x in zip(threads, posts)]

    return render_template('board_index.html',
            board            = board,
            boardsum         = boardsum,
            time             = time )

@app.route("/thread/<int:thread_id>")
def board_thread(thread_id):
    posts = get_thread_posts(thread_id)
    thread = get_thread_by_id(thread_id)

    return render_template('thread.html',
            thread = thread,
            posts  = posts,
            board  = get_board_name(thread["board"]),
            time   = time )

@app.route("/post-thread/<board>", methods=["POST"])
def create_new_thread(board):
    if request.method == 'POST':
        print( "got subject:" + request.form["subject"] + "\ngot content:" + request.form["content"] )

        board_id = get_board_id( board )

        if board_id == None:
            abort(404)
        else:
            board_id = board_id[0]

        subject = request.form["subject"]
        if subject == "":
            subject = "<no subject>"

        db = get_db()
        db.execute("insert into threads(board, subject, hidden) values (?,?,?)",
                   (board_id, subject,0))

        thread_id = get_max_thread_number()

        add_post(thread_id, "Anonymous", request.form["content"])
        db.commit()

        return redirect(request.host_url + "thread/" + str(thread_id))

    else:
        return 'huh?'

@app.route("/reply/<int:thread_id>", methods=["POST"])
def reply_to_thread(thread_id):
    if request.method == "POST":
        add_post(thread_id, request.form["name"], request.form["content"])
        update_thread_time(thread_id)

        return redirect(request.host_url + "thread/" + str(thread_id))

    else:
        return "huh?"

@app.route("/create-board", methods=["POST"])
def create_board():
    if request.method == 'POST':
        thing = get_board_id(request.form["name"])

        print(thing)
        if thing == None:
            add_board( request.form["name"], request.form["description"])
            return redirect(request.host_url + request.form["name"])

        else:
            return status_page("Board already exists!", "Please select a unique name.")

    else:
        return 'huh?'

@app.route("/admin/reported")
def admin_reported():
    return render_template('admin.html',
            flagged_posts  = get_flagged_posts(),
            time           = time )

@app.route("/admin/hidden")
def admin_hidden():
    return render_template('admin.html',
            flagged_posts  = get_hidden_posts(),
            time           = time )

@app.route("/flag-post/<int:post_id>", methods=["GET"])
def flag_post(post_id):
    db = get_db()
    db.execute("update posts set flagged=1 where id=?", (post_id,))
    db.commit()

    return status_page("Post flagged", "Post has been flagged for moderation.")

@app.route("/unflag-post/<int:post_id>", methods=["GET"])
def unflag_post(post_id):
    db = get_db()
    db.execute("update posts set flagged=0 where id=?", (post_id,))
    db.execute("update posts set hidden=0 where id=?", (post_id,))
    db.commit()

    return status_page("Post unflagged", "Post has been unflagged.")

@app.route("/hide-post/<int:post_id>", methods=["GET"])
def hide_post(post_id):
    db = get_db()
    db.execute("update posts set hidden=1 where id=?", (post_id,))
    db.execute("update posts set flagged=0 where id=?", (post_id,))
    db.commit()

    return status_page("Post hidden", "Post has been hidden.")

def get_thread_by_id( thread_id ):
    db = get_db()
    row = db.execute("select * from threads where id=?", (thread_id,))
    return row.fetchone()

def get_post_by_id( post_id ):
    db = get_db()
    row = db.execute("select * from posts where id=?", (post_id,))
    return row.fetchone()

def get_flagged_posts():
    db = get_db()
    row = db.execute("select * from posts where flagged=1")
    return row.fetchall()

def get_hidden_posts():
    db = get_db()
    row = db.execute("select * from posts where hidden=1")
    return row.fetchall()

def get_board_threads( board_id ):
    db = get_db()

    row = db.execute("""
        select * from threads
            where board=?
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

def get_board_name(id):
    db = get_db()
    row = db.execute("select name from boards where id=?", (id,))
    return row.fetchone()["name"]

def get_thread_posts( thread_id ):
    db = get_db()

    row = db.execute("""
        select * from posts
        where thread=?
        order by id asc
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

def summarize_thread( posts, sum_size=4 ):
    if len(posts) > sum_size:
        omitted = len(posts) - sum_size

        print( "ommited " + str(omitted) + " posts")

        return ([posts[0]] + posts[-sum_size + 1:], omitted)

    else:
        return (posts, 0)

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

    db.execute("""
        insert into posts(thread, name, content, post_time, flagged, hidden)
            values (?,?,?,?,0,0)
    """, (thread_id, name, escaped, time.time()))

    post_id = get_max_post_number()

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
        update threads
            set last_updated=?
            where id=?
    """, (time.time(), thread_id,))

    db.commit()

def status_page(summary, text, path="/"):
    return render_template('status.html', status =
        {
            "summary":    summary,
            "text":       text,
            "return_url": request.host_url + path
        })

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

@app.cli.command('initdb')
def setup_db():
    db = get_db()

    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())

    config = open('config.yaml', 'r')
    configs = yaml.load(config)
    boards = configs['boards']

    for name in boards:
        desc = boards[name]
        db.execute("""
            insert into boards(name, description)
                values (?,?)
        """, (name, desc))

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
