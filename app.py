from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import datetime
import random
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
    user = session.get('user')
    return render_template('mainpage.html', user=user)

@app.route('/listing/<int:listing_id>', methods=['GET'])
def listing_detail(listing_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # product + seller info to be displayed on the page
    cursor.execute('''
        SELECT pl.Product_Title, pl.Product_Description, pl.Product_Price, pl.Quantity, s.business_name
        FROM product_listings pl
        JOIN sellers s ON pl.Seller_Email = s.email
        WHERE pl.Listing_ID = ?
    ''', (listing_id,))

    result = cursor.fetchone()
    connection.close()

    if result:
        product = {
            'title': result[0],
            'description': result[1],
            'price': result[2],
            'quantity': result[3],
            'seller_name': result[4],
            'listing_id': listing_id
        }
        return render_template('listing.html', product=product)
    else:
        return "Product not found", 404

@app.route('/order_review/<int:listing_id>', methods=['GET', 'POST'])
def order_review(listing_id):
    # user should be a logged-in buyer before being able to buy a product
    if 'user' not in session or session['user']['role'] != 'buyer':
        return redirect(url_for('login_form'))

    user_email = session['user']['email']
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # product + seller info to be displayed on the page
    cursor.execute('''
        SELECT pl.Product_Title, pl.Product_Description, pl.Product_Price, pl.Quantity, pl.Seller_Email, s.business_name
        FROM product_listings pl
        JOIN sellers s ON pl.Seller_Email = s.email
        WHERE pl.Listing_ID = ?
    ''', (listing_id,))
    product = cursor.fetchone()

    if not product:
        connection.close()
        return "Product not found", 404

    # gets all credit cards for saved info
    cursor.execute('''SELECT credit_card_num, card_type FROM credit_cards WHERE Owner_email = ?''', (user_email,))
    cards = cursor.fetchall()
    connection.close()

    product_data = {
        'title': product[0],
        'description': product[1],
        'price': product[2],
        'available': product[3],
        'seller_email': product[4],
        'seller_name': product[5],
        'listing_id': listing_id
    }

    return render_template('order_review.html', product=product_data, cards=cards)


def generate_unique_order_id(cursor):
    while True:
        order_id = random.randint(100, 999999)  # 3 to 6-digit number
        cursor.execute('SELECT 1 FROM orders WHERE Order_ID = ?', (order_id,))
        if not cursor.fetchone():
            return order_id

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user' not in session or session['user']['role'] != 'buyer':
        return redirect(url_for('login_form'))

    buyer_email = session['user']['email']
    listing_id = request.form['listing_id']
    quantity = int(request.form['quantity'])
    card = request.form['card']
    seller_email = request.form['seller_email']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    order_id = generate_unique_order_id(cursor)
    now = datetime.datetime.now()
    date_str = f"{now.year}/{now.month}/{now.day}"

    cursor.execute('SELECT Product_Price, Quantity FROM product_listings WHERE Listing_ID = ?', (listing_id,))
    product = cursor.fetchone()

    if not product or quantity > product[1]:
        connection.close()
        return "Invalid quantity", 400

    price_string = str(product[0]).replace('$', '').strip()
    price = float(price_string)
    total_payment = round(price * quantity, 2)
    new_quantity = product[1] - quantity

    # adds a new order to the table
    cursor.execute('''
        INSERT INTO orders (Order_ID, Seller_Email, Listing_ID, Buyer_Email, Date, Quantity, Payment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, seller_email, listing_id, buyer_email, date_str, quantity, total_payment))

    # if the new quantity is 0, set the status to be 2. otherwise, status is unchanged
    cursor.execute('''
        UPDATE product_listings
        SET Quantity = ?, Status = CASE WHEN ? = 0 THEN 2 ELSE Status END
        WHERE Listing_ID = ?
    ''', (new_quantity, new_quantity, listing_id))

    # update seller balance depending on the order
    cursor.execute('''
        UPDATE sellers SET balance = balance + ? WHERE email = ?
    ''', (total_payment, seller_email))

    connection.commit()
    connection.close()

    return redirect(url_for('mainpage'))

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
