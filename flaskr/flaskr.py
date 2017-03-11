# -*- coding: utf-8 -*-
"""
    SealnoteFlaskr
    ~~~~~~

    A wrapper around sealnote db using flaskr example code

        A microblog example application written as Flask tutorial with
        Flask and sqlite3.

        :copyright: (c) 2015 by Armin Ronacher.
        :license: BSD, see LICENSE for more details.
"""

import os
from pysqlcipher3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from datetime import datetime


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '../db/testdb'),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.before_request
def limit_remote_addr():
    if request.remote_addr != '127.0.0.1':
        abort(403)  # Forbidden

def connect_db(password):
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.cursor().execute('PRAGMA KEY = "%s"' % password);
    rv.row_factory = sqlite3.Row
    return rv

def get_db(password):
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db(password)
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    if 'password' not in session:
        return redirect(url_for('login'))

    db = get_db(session['password'])
    cur = db.execute('select title, content as text from notes order by created desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db(session['password'])
    # From java code
    #    SQLiteDatabase db = this.getWritableDatabase();
    #    ContentValues values = new ContentValues();
    #    EasyDate date = EasyDate.now();

    #    values.put(COL_POSITION, note.getPosition());
    #    values.put(COL_TITLE, note.getTitle());
    #    values.put(COL_NOTE, note.getNote().toString());
    #    values.put(COL_COLOR, note.getColor());
    #    values.put(COL_CREATED, date.toString());
    #    values.put(COL_EDITED, date.toString());
    #    values.put(COL_ARCHIVED, note.getIsArchived() ? 1 : 0);
    #    values.put(COL_DELETED, note.getIsDeleted() ? 1 : 0);
    #    values.put(COL_TYPE, note.getType().name());
    #    values.put(COL_NOTE_EXTRA, note.getNote().getCardString());

    title = request.form['title']
    content = request.form['text']
    if not title or not content:
        return abort(400)

    extra = content
    created = datetime.utcnow().isoformat() + " UTC"
    edited = created
    
    db.execute(
            ('INSERT INTO notes '
            '(position, title, content, color, created, '
            'edited, content_extra) '
            'VALUES (-1, ?, ?, 0, ?, ?, ?)'),
               (title, content, created, edited, extra))
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        session['password'] = request.form['password']
        session['logged_in'] = True
        flash('You were logged in')
        return redirect(url_for('show_entries'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('password', None)
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
        del g.sqlite_db
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == "__main__":
    app.run()
