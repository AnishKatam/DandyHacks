from flask import Flask, redirect, render_template, url_for, make_response, send_from_directory, request
import database
import html
import secrets
import datetime
import bcrypt

app = Flask(__name__)


@app.route('/<path:path>')
def send_static(path):
    response = make_response(send_from_directory('static', path), 200)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.route('/')
def index():
    token = request.cookies.get('auth', None)
    if token and database.check_token(token):
        response = make_response(
            redirect(url_for('dashboard', _external=True)))
        response.set_cookie('auth', token)
        return response
    return render_template('pages/index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    # Check if user is already logged in
    token = request.cookies.get('auth', None)
    if token is not None and database.check_token(token):
        response = make_response(redirect(url_for('index', _external=True)))
        response.set_cookie('auth', token)
        return response

    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username:
            error = 'Username Empty'
        elif not password:
            error = 'Password Empty'
        else:
            username = html.escape(username)
            user = database.get_user_by_username(username)
            if user is None:
                error = 'No User Found'
            else:
                # Verify password
                ph = bcrypt.hashpw(password.encode(), user.salt)
                if ph == user.passhash:
                    token = secrets.token_hex()
                    database.set_user_token(
                        username, token, datetime.datetime.now(tz=datetime.timezone.utc)
                    )
                    response = make_response(redirect(url_for('index', _external=True)))
                    response.set_cookie('auth', token)
                    return response
                else:
                    error = 'Password Incorrect'
        
        # If there's an error, render the index page with the error message
        response = make_response(render_template('index.html', error=error))
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    # For GET requests, render the index page with no error
    response = make_response(render_template('index.html', error=''))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


app.run(debug=True, host='127.0.0.1', port=8080)
