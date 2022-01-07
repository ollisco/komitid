"""
Created on 2020-08-27
Fläsk
Project: komitid
@author: ollejernstrom
"""

# Libraries and frameworks
from flask import abort, Flask, flash, g, render_template, redirect, request, url_for, session
import pickle
from db_models import checkuser, get_data, get_session_user, db_query, create_user, create_profile, get_profile
from api_models import Trip, sl_search, sl_get_trip, KomitidProfil, get_google_api_credentials, get_google_api_link

# Setup
app = Flask(__name__)
app.secret_key = 'ennyckeljävelbarajagkan'


@app.before_request
def before_request():
    if 'user_id' in session:
        user = get_session_user(session['user_id'])
        g.user = user


@app.route('/home', methods=['GET', 'POST'])
def home():
    if not hasattr(g, 'user'):
        return redirect(url_for('login'))
    return render_template('sites/home.html')


@app.route('/sltrip', methods=['GET', 'POST'])
def sltrip():
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')

        g.sl = sl_get_trip(origin, destination, '09:00')

    return render_template('sites/sltrip.html')


@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if request.method == 'POST':
        home = request.form.get('hem')
        school = request.form.get('skola')
        time_before_trip = request.form.get('tid')
        code = request.form.get('token')

        prof = KomitidProfil(g.user.id, get_google_api_credentials(
            code), home, school, time_before_trip)

        if get_profile(g.user.id) == -1:
            create_profile(g.user.id, prof)

        return redirect(url_for('alarm'))
    g.link = get_google_api_link()

    return render_template('sites/profil_create.html')


@app.route('/alarm', methods=['GET', 'POST'])
def alarm():
    g.profile = get_profile(g.user.id)
    return render_template('sites/alarm.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        existing_usernames = [x[0] for x in db_query('Username')]

        if username not in existing_usernames and password == re_password:
            create_user(username, password)
            print('User Created')
            return redirect(url_for('login'))
        print('Could not create account')

    return render_template('sites/signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('user_id', None)
    if request.method == 'POST':
        # Removes existing user

        # Gets form data
        uname = request.form.get('username')
        pword = request.form.get('password')

        # Checks if user exists
        userid = checkuser(uname, pword)
        if userid:
            session['user_id'] = userid
            print(0)
            return redirect(url_for('home'))

    return render_template('sites/login.html')


@app.route('/')
def index():
    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('user_id', None)


if __name__ == '__main__':
    app.run(debug=True)
