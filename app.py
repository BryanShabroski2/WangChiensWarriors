from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
app = Flask(__name__)

db_path = 'WCW.sqlite'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/success')
def success():
    return render_template('success.html')



@app.route('/login', methods=['POST'])
def login():
    email = request.form['Email']
    password = request.form['Password']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT hashed_password FROM users WHERE email = ?', (email,))
    result = cursor.fetchone()
    connection.close()

    if result is None:
        return render_template('index.html', error='Invalid email or password.')

    hashed_password = result[0]

    if check_password_hash(hashed_password, password):
        return redirect(url_for('success'))
    else:
        return render_template('index.html', error='Invalid email or password.')




if __name__ == '__main__':
    app.run(debug=True)
