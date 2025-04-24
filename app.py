from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
app = Flask(__name__)
app.secret_key = 'dev'
db_path = 'WCW.sqlite'

def get_user_role(email):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    for table in ['buyers', 'sellers', 'helpdesk']:
        cursor.execute(f"SELECT 1 FROM {table} WHERE email = ?", (email,))
        if cursor.fetchone():
            connection.close()
            if table == 'buyers':
                return 'buyer'
            elif table == 'sellers':
                return 'seller'
            elif table == 'helpdesk':
                return 'helpdesk'

    connection.close()
    return None  # fallback if role not found



@app.route('/')
def mainpage():
    # Old root directory, now we redirect to the main page
    # return render_template('login.html')
    return render_template('mainpage.html')

@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

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
        return render_template('login.html', error='Invalid email or password.')

    hashed_password = result[0]

    if check_password_hash(hashed_password, password):
        role = get_user_role(email)
        session['user'] = {
            'email': email,
            'role': role
        }
        return redirect(url_for('mainpage', success='Logged in successfully!'))

    else:
        return render_template('login.html', error='Invalid email or password.')

@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

# User registration process form
@app.route('/register', methods=['POST'])
def register():
    #Get email password and role from form
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    role = request.form['role']

    #Make sure confirmed password matches
    if password != confirm_password:
        return render_template('register.html', error='Passwords do not match.')
    #Generate a hashed password
    hashed_password = generate_password_hash(password)
    #Connect to the database and connect the cursor
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #Make sure user does not already exist
    cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        connection.close()
        return render_template('register.html', error='Email already registered.')

    #Insert into users table
    cursor.execute(
        'INSERT INTO users (email, hashed_password) VALUES (?, ?)',
        (email, hashed_password)
    )

    #Based on role we insert that form information into the database
    if role == 'buyer':
        business_name = request.form['business_name']
        buyer_address_id = request.form['buyer_address_id']

        cursor.execute(
            'INSERT INTO buyers (email, business_name, buyer_address_id) VALUES (?, ?, ?)',
            (email, business_name, buyer_address_id)
        )

    elif role == 'seller':
        business_name = request.form['business_name']
        business_address_id = request.form['business_address_id']
        bank_routing_number = request.form['bank_routing_number']
        bank_account_number = request.form['bank_account_number']

        cursor.execute(
            'INSERT INTO sellers (email, business_name, Business_Address_ID, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?, ?, ?)',
            (email, business_name, business_address_id, bank_routing_number, bank_account_number, 0.0)
        )

    elif role == 'helpdesk':
        position = request.form['position']

        cursor.execute(
            'INSERT INTO helpdesk (email, Position) VALUES (?, ?)',
            (email, position)
        )
    #Close
    connection.commit()
    connection.close()

    #Automatically log in user.
    session['user'] = {
        'email': email,
        'role': role
    }

    #redirect to mainpage
    return redirect(url_for('mainpage'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('mainpage'))
@app.route('/profile', methods=['GET'])
def profile():
    if 'user' not in session:
        return redirect(url_for('mainpage'))

    # Get user data
    user_email = session['user']['email']
    role = session['user']['role']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    user_data = {}
    if role == 'buyer':
        # Only fetch the specific fields we need
        cursor.execute('SELECT business_name, buyer_address_id FROM buyers WHERE email = ?', (user_email,))
        result = cursor.fetchone()
        if result:
            user_data = {
                'business_name': result[0],
                'buyer_address_id': result[1]
            }
    elif role == 'seller':
        # Only fetch the specific fields we need
        cursor.execute('SELECT business_name, Business_Address_ID, bank_routing_number, bank_account_number, balance FROM sellers WHERE email = ?', (user_email,))
        result = cursor.fetchone()
        if result:
            user_data = {
                'business_name': result[0],
                'Business_Address_ID': result[1],
                'bank_routing_number': result[2],
                'bank_account_number': result[3],
                'balance': result[4]
            }
    elif role == 'helpdesk':
        #Get our user data f
        cursor.execute('SELECT Position FROM helpdesk WHERE email = ?', (user_email,))
        result = cursor.fetchone()
        if result:
            user_data = {
                'Position': result[0]
            }

    connection.close()

    return render_template('profile.html', user=session['user'], user_data=user_data)



@app.route('/profile/update', methods=['POST'])
def profile_update():
    #Make sure user is loggedin
    if 'user' not in session:
        return redirect(url_for('mainpage'))

    user_email = session['user']['email']
    role = session['user']['role']

    #Connect to DB
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #See what type of user, and make changes accordingly. Password is for all, and the rest are role specific
    if request.form.get('new_password') and request.form.get('confirm_password'):
        if request.form['new_password'] != request.form['confirm_password']:
            connection.close()
            return redirect(url_for('profile', error='Passwords do not match'))

        # Hash the new password
        hashed_password = generate_password_hash(request.form['new_password'])
        cursor.execute('UPDATE users SET hashed_password = ? WHERE email = ?',
                       (hashed_password, user_email))

    if role == 'buyer':
        business_name = request.form['business_name']

        cursor.execute('UPDATE buyers SET business_name = ? WHERE email = ?',
                       (business_name, user_email))

    elif role == 'seller':
        business_name = request.form['business_name']
        bank_routing_number = request.form['bank_routing_number']
        bank_account_number = request.form['bank_account_number']

        cursor.execute('''
            UPDATE sellers 
            SET business_name = ?, bank_routing_number = ?, bank_account_number = ? 
            WHERE email = ?
        ''', (business_name, bank_routing_number, bank_account_number, user_email))

    elif role == 'helpdesk':
        position = request.form['position']

        cursor.execute('UPDATE helpdesk SET Position = ? WHERE email = ?',
                       (position, user_email))

    connection.commit()
    connection.close()

    return redirect(url_for('profile', success='Profile updated successfully'))

#for requesting email change
@app.route('/email/change', methods=['POST'])
def email_change_request():
    #make sure user is logged in
    if 'user' not in session:
        return redirect(url_for('mainpage'))

    user_email = session['user']['email']
    new_email = request.form['new_email']
    reason = "ChangeID"

    #connect to database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #Create a unique ID for the ECR (Email change request)
    import time
    import random
    request_id = f"ECR{int(time.time())}{random.randint(1000, 9999)}"

    #insert into requests table
    cursor.execute('''
        INSERT INTO requests 
        (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request_id, user_email, None, "EMAIL_CHANGE", f"New email: {new_email}\nReason: {reason}", "PENDING"))

    connection.commit()
    connection.close()

    return redirect(url_for('profile', success='Email change request submitted and pending approval'))

@app.route('/search')
def search():
    # Temporary placeholder – this can be replaced later
    query = request.args.get('q', '')
    return f"Search not implemented yet. You searched for: {query}"

if __name__ == '__main__':
    app.run(debug=True)
