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
     render_template, flash, Markup
import markdown
from datetime import datetime

from remote import DropboxRemote

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '../db/testdb'),
    DEBUG=True,
    SECRET_KEY=os.urandom(32).hex(),
    DROPBOX_ACCESS_TOKEN=None,
    DROPBOX_PATH=None
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

if app.config['DROPBOX_ACCESS_TOKEN']:
    print("Setting up dropbox remote with remote Dropbox:/", app.config['DROPBOX_PATH'])
    remote = DropboxRemote(
            app.config['DROPBOX_ACCESS_TOKEN'],
            app.config['DATABASE'],
            app.config['DROPBOX_PATH'])

def loadRemoteDatabase():
    if app.config['DROPBOX_ACCESS_TOKEN']:
        remote.load()

def saveRemoteDatabase():
    if app.config['DROPBOX_ACCESS_TOKEN']:
        remote.save()

@app.before_request
def limit_remote_addr():
    if '192.168' not in request.remote_addr and '127.0.0.1' != request.remote_addr:
        print("Blocking ", request.remote_addr)
        abort(403)  # Forbidden

def connect_db(password):
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    print("Connecting to:", app.config['DATABASE'])
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


@app.route('/note/<int:note_id>')
def show_entry(note_id):
    print(note_id, type(note_id))

    if 'password' not in session:
        return redirect(url_for('login'))

    db = get_db(session['password'])
    cur = db.execute(
          'SELECT _id, title, content AS text, created FROM notes WHERE _id = ?',
          (note_id, ))
    entries = cur.fetchall()
    entry = entries[0]
    result = {
            'id': entry['_id'],
            'title': entry['title'],
            'text': entry['text'],
            'created': entry['created']
    }

    return render_template('entry.html', entry=result)


@app.route('/', defaults={'page': 0})
@app.route('/<int:page>')
def show_entries(page):
    if 'password' not in session:
        return redirect(url_for('login'))

    itemsPerPage = 10
    db = get_db(session['password'])
    cur = db.execute(
      'SELECT _id, title, content AS text, created FROM notes ORDER BY created DESC LIMIT ? OFFSET ?',
      (itemsPerPage, itemsPerPage*page))
    entries = cur.fetchall()

    marked_entries = []

    for entry in entries:
        word_count = len(entry['text'].split())
        marked_entries.append({
            'id': entry['_id'],
            'title': entry['title'],
            'text': Markup(markdown.markdown(entry['text'])),
            'word_count': word_count,
            'created': entry['created']
        })

    return render_template('show_entries.html', entries=marked_entries)


@app.route('/update', methods=['POST'])
def update_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db(session['password'])

    noteid = request.form['id']
    title = request.form['title']
    content = request.form['text']
    if not title or not content:
        return abort(400)

    extra = content
    edited = datetime.utcnow().isoformat() + " UTC"
    
    db.execute(
            ('UPDATE notes '
            'SET title = ?, '
            'content = ?, '
            'edited = ?, '
            'content_extra = ? '
            'WHERE _id = ?'),
               (title, content, edited, extra, noteid))
    db.commit()

    if (app.config['DEBUG']):
        print(title, content, edited, extra)

    flash('Entry was updated')
    return redirect(url_for('show_entries'))


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

    if (app.config['DEBUG']):
        print(title, content, created, edited, extra)

    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('hardload'):
            loadRemoteDatabase() # its a no-op if remote not setup

        password = request.form['password']
        try:
            # test password
            db = get_db(password)
            cur = db.execute('select title from notes LIMIT 1')
            cur.close()
        except:
            return render_template('login.html', error="Wrong password")
        # if nothing threw, proceed
        session['password'] = password
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

    saveRemoteDatabase() #its a no-op if rremote not setup
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', ssl_context='adhoc')
