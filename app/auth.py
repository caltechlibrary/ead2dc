import functools

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

'''
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')
'''

@bp.route('/login', methods=('GET', 'POST'))
def login():
    username, user_email = authorize_user()
    if user_email:
        g.user = user_email
    else:
        g.user = None
    return render_template('index.html')
    '''
    if request.method == 'POST':
        username = request.form['username']
        #password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        #elif not check_password_hash(user['password'], password):
        #using plain text passwords for now
        #elif user['password'] != password:
        #    error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')
    '''

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def authorize_user():
    # REMOTE_USER is an email address in Shibboleth
    email_address = request.environ["REMOTE_USER"]
    if '@caltech.edu' in email_address:
        username = email_address[:email_address.find('@caltech.edu')]
    else:
        username = email_address
    # we check the username against our authorized users
    query = "SELECT username FROM user WHERE username = ?;"
    db = get_db()
    if db.execute(query, [email_address]).fetchone():
        return username, email_address
    else:
        return None, None