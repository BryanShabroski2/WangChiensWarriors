from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import datetime
import random
import time
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

def get_children_categories(cursor, parent_category):
    cursor.execute('''
            SELECT category_name FROM categories
            WHERE parent_category = ?
        ''', (parent_category,))
    children = [row[0] for row in cursor.fetchall()]
    return children

def dfs_category(start_category):
    result = []
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    def dfs(current_category):
        result.append(current_category)
        children = get_children_categories(cursor, current_category)
        for child in children:
            dfs(child)
    dfs(start_category)
    connection.close()
    return result

# if user is a buyer or seller, look up their business name in their respective table
def get_user_business_name(email, role):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    if role == 'buyer':
        cursor.execute("SELECT business_name FROM buyers WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    elif role == 'seller':
        cursor.execute("SELECT business_name FROM sellers WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    # helpdesk staff don't have a business name
    elif role == 'helpdesk':
        return None

    connection.close()
    return None

# gets the seller's rating from seller email
def get_seller_rating(seller_email):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # calculates and selects the average rating for the given seller by joining reviews and orders
    cursor.execute('''
        SELECT AVG(Rate)
        FROM reviews
        JOIN orders ON reviews.Order_ID = orders.Order_ID
        WHERE orders.Seller_Email = ?
    ''', (seller_email,))
    result = cursor.fetchone()
    connection.close()

    # if there is at least 1 rating, round the average to 2 decimal places
    if result and result[0]:
        return round(result[0], 2)
    else:
        return None

@app.route('/')
@app.route('/category/<string:category>')
@app.route('/category/<string:category>/<string:subcategory>')
@app.route('/category/<string:category>/<string:subcategory>/<string:subsubcategory>')
def mainpage(category="All", subcategory="", subsubcategory=""):
    user = session.get('user')

    # Gets the requested page from the request args
    page = request.args.get('page', 1, type=int)

    # The number of listings per page
    PAGE_SIZE = 60


    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # To form queries, we create base SQL queries and append onto them depending on
    # the search filters and things like category and subcategory
    count_query = '''
        SELECT count(*)
        FROM product_listings p
        JOIN categories c ON p.Category = c.category_name
        WHERE p.Status = 1
    '''

    data_query = '''
        SELECT 
            p.Product_Title, 
            p.Product_Name, 
            s.Business_Name,
            p.Listing_ID, 
            p.Quantity, 
            p.Product_Price,
            p.Seller_Email
        FROM product_listings p, sellers s, categories c
        WHERE p.Status = 1 
          AND p.Seller_Email = s.email
          AND p.Category = c.category_name
    '''

    # filters refer the string clauses we add to build the query
    # params refer to the actual variables we are inserting into the query
    # where params[i] corresponds to the ith question mark in the query
    filters = []
    params = []
    parent_category = ""

    if subsubcategory:
        filters.append('p.Category = ?')
        params.append(subsubcategory)
        parent_category = subsubcategory
    elif subcategory:
        all_descendants = dfs_category(subcategory)
        # Creates a SQL check where the category must be in the list of all descendants
        # (by doing a DFS traversal of children nodes)
        # This makes sure selecting a parent category displays all products
        filters.append('p.Category IN (' + ','.join(['?'] * len(all_descendants)) + ')')
        params.extend(all_descendants)
        parent_category = subcategory
    elif category != "All":
        all_descendants = dfs_category(category)
        filters.append('p.Category IN (' + ','.join(['?'] * len(all_descendants)) + ')')
        params.extend(all_descendants)
        parent_category = category
    else:
        parent_category = "Root"

    if filters:
        # join our filters with ANDs
        count_query += ' AND ' + ' AND '.join(filters)
        data_query += ' AND ' + ' AND '.join(filters)

    cursor.execute(count_query, tuple(params))
    total_listings = cursor.fetchone()[0]
    total_pages = (total_listings + PAGE_SIZE - 1) // PAGE_SIZE

    # Make sure pages don't go out of bounds
    if page > total_pages:
        page = total_pages
    elif page < 1:
        page = 1

    offset = (page - 1) * PAGE_SIZE

    data_query += ' ORDER BY p.Listing_ID LIMIT ? OFFSET ?'
    data_params = params + [PAGE_SIZE, offset]

    cursor.execute(data_query, tuple(data_params))
    listings = cursor.fetchall()

    # For category listing on the navbar
    cursor.execute('''
        SELECT category_name
        FROM categories
        WHERE parent_category = ?
    ''', (parent_category,))
    categories = cursor.fetchall()

    # each listing now incorporates all details about the product listing
    enhanced_listings = []
    for listing in listings:
        product_title, product_name, business_name, listing_id, quantity, price, seller_email = listing
        seller_rating = get_seller_rating(seller_email)
        enhanced_listings.append((product_title, product_name, business_name, listing_id, quantity, price, seller_email, seller_rating))

    return render_template('mainpage.html',
                           listings=enhanced_listings,
                           categories=categories,
                           category=category,
                           subcategory=subcategory,
                           subsubcategory=subsubcategory,
                           page=page,
                           total_pages=total_pages,
                           user=user
                           )

# page for the listing details
@app.route('/listing/<int:listing_id>', methods=['GET'])
def listing_detail(listing_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # product + seller info to be displayed on the page
    cursor.execute('''
        SELECT pl.Product_Title, pl.Product_Name, pl.Product_Description, pl.Product_Price, pl.Quantity, s.business_name, s.email
        FROM product_listings pl
        JOIN sellers s ON pl.Seller_Email = s.email
        WHERE pl.Listing_ID = ?
    ''', (listing_id,))

    result = cursor.fetchone()
    connection.close()

    # if a matching product was found, map the query result into structured product dictionary
    if result:
        product = {
            'title': result[0],
            'name': result[1],
            'description': result[2],
            'price': result[3],
            'quantity': result[4],
            'seller_name': result[5],
            'seller_email': result[6],
            'listing_id': listing_id
        }
        # calculate seller rating which needs to be displayed on the detailed product listing page
        seller_rating = get_seller_rating(result[6])
        return render_template('listing.html', product=product, seller_rating=seller_rating)

    else:
        return "Product not found", 404

# page for detailed seller information
@app.route('/seller/<seller_name>')
def seller_detail(seller_name):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # gets seller's business name and email from seller table based on seller's business name
    cursor.execute('''
        SELECT business_name, email
        FROM sellers
        WHERE business_name = ?
    ''', (seller_name,))
    seller = cursor.fetchone()

    # if no seller exists with that business name and email, return 404 not found
    if not seller:
        connection.close()
        return "Seller not found", 404
    seller_rating = get_seller_rating(seller[1])

    # retrieve all rating and descriptions for this seller by joining reviews and orders where order IDs match
    cursor.execute('''
        SELECT r.Rate, r.Review_Desc
        FROM reviews r
        JOIN orders o ON r.Order_ID = o.Order_ID
        WHERE o.Seller_Email = (
            SELECT email
            FROM sellers
            WHERE business_name = ?
        )
    ''', (seller_name,))
    reviews = cursor.fetchall()

    connection.close()

    return render_template('seller.html', seller=seller, reviews=reviews, seller_rating=seller_rating)

# page for secure checkout. user is taken here after confirming what they want to buy
@app.route('/secure_checkout', methods=['POST'])
def secure_checkout():
    # user should be a logged-in buyer before being able to buy a product
    if 'user' not in session or session['user']['role'] != 'buyer':
        return redirect(url_for('login_form'))

    # from session data, retrieve buyer's email
    user_email = session['user']['email']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # get the listing ID and quantity from the form submission
    listing_id = request.form.get('listing_id')
    quantity = request.form.get('quantity')

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

    # if the user enters a new card, collect all new card details if provided via the form
    new_card_number = request.form.get('new_card_number')
    card_type = request.form.get('card_type')
    expire_month = request.form.get('expire_month')
    expire_year = request.form.get('expire_year')
    security_code = request.form.get('security_code')

    # if the user entered all info for a new card, insert into the credit_cards table. also done in place_order
    if new_card_number and card_type and expire_month and expire_year and security_code:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_card_number, card_type, expire_month, expire_year, security_code, session['user']['email']))

        connection.commit()
        connection.close()

    # product data dictionary for rendering in the html
    product_data = {
        'title': product[0],
        'description': product[1],
        'price': product[2],
        'available': product[3],
        'seller_email': product[4],
        'seller_name': product[5],
        'listing_id': listing_id
    }

    # converts price string to float and calculates total price based on quantity
    price_string = str(product[2]).replace('$', '').replace(',', '').strip()
    price = float(price_string)
    total_price = round(price * int(quantity), 2)

    # get seller's rating from email for display on checkout page
    seller_rating = get_seller_rating(product[4])

    return render_template('secure_checkout.html', listing_id=listing_id, product=product_data, cards=cards, quantity=quantity, total_price=total_price, seller_rating=seller_rating, seller_name=product[5])

# page for user to confirm what they want to buy
@app.route('/order_review/<int:listing_id>', methods=['GET'])
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
    connection.close()

    if not product:
        return "Product not found", 404

    # product data dictionary for rendering in the html
    product_data = {
        'title': product[0],
        'description': product[1],
        'price': product[2],
        'available': product[3],
        'seller_email': product[4],
        'seller_name': product[5],
        'listing_id': listing_id
    }

    # get seller's rating from email for display on order review page
    seller_rating = get_seller_rating(product[4])

    return render_template('order_review.html', product=product_data, seller_rating=seller_rating, seller_name=product[5])

# creates a unique order ID ranging from a 3 to 6 digit number
def generate_unique_order_id(cursor):
    while True:
        order_id = random.randint(100, 999999)  # 3 to 6-digit number
        cursor.execute('SELECT 1 FROM orders WHERE Order_ID = ?', (order_id,))
        if not cursor.fetchone():
            return order_id

@app.route('/place_order', methods=['POST'])
def place_order():
    # user must be a logged-in buyer to buy products
    if 'user' not in session or session['user']['role'] != 'buyer':
        return redirect(url_for('login_form'))

    # get buyer email from the session
    buyer_email = session['user']['email']

    # get listing details from the form
    listing_id = request.form['listing_id']
    quantity = int(request.form['quantity'])
    seller_email = request.form['seller_email']

    # get new payment details from new credit card form if entered
    card = request.form.get('card')
    new_card_number = request.form.get('new_card_number')
    card_type = request.form.get('card_type')
    expire_month = request.form.get('expire_month')
    expire_year = request.form.get('expire_year')
    security_code = request.form.get('security_code')

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # get the product price and current available quantity
    cursor.execute('SELECT Product_Price, Quantity FROM product_listings WHERE Listing_ID = ?', (listing_id,))
    product = cursor.fetchone()

    # if the product does not exist or the quantity requested is greater than the available quantity, this is invalid and returns 400
    if not product or quantity > product[1]:
        connection.close()
        return "Invalid quantity", 400

    # converts price string to float and calculates total price based on quantity
    price_string = str(product[0]).replace('$', '').replace(',', '').strip()
    price = float(price_string)
    total_payment = round(price * quantity, 2)
    new_quantity = product[1] - quantity

    # if a new credit card number was provided, insert all relevant details into the credit_cards table
    if new_card_number and card_type and expire_month and expire_year and security_code:
        cursor.execute('''
            INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_card_number, card_type, expire_month, expire_year, security_code, buyer_email))

    # generate unique order id and time stamp for the order
    order_id = generate_unique_order_id(cursor)
    now = datetime.datetime.now()
    date_str = f"{now.year}/{now.month}/{now.day}"

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

    return redirect(url_for('order_confirmation', order_id=order_id))

# page for order confirmation after the user places an order
@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'user' not in session or session['user']['role'] != 'buyer':
        return redirect(url_for('login_form'))

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # product + seller info to be displayed on the page
    cursor.execute('''
        SELECT p.Product_Title, o.Quantity, o.Payment, o.Seller_Email
        FROM orders o
        JOIN product_listings p ON o.Listing_ID = p.Listing_ID
        WHERE o.Order_ID = ?
    ''', (order_id,))
    order = cursor.fetchone()
    connection.close()

    # if no order found, return a 404
    if not order:
        return "Order not found", 404

    # product dictionary containing the title
    product = {
        'title': order[0]
    }
    # from query results, get all relevant details for the order
    quantity = order[1]
    total_payment = order[2]
    seller_email = order[3]
    seller_rating = get_seller_rating(seller_email)

    return render_template('order_confirmation.html', order_id=order_id, product=product, quantity=quantity, total_payment=total_payment, seller_rating=seller_rating)

@app.route('/submit_review/<int:order_id>', methods=['POST'])
def submit_review(order_id):
    # user should be a logged-in buyer
    if 'user' not in session or session['user']['role'] != 'buyer':
        return redirect(url_for('login_form'))

    # retrieve the rating /5 and description from the form
    rate = int(request.form['rate'])
    review_desc = request.form['review_desc']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # insert the relevant details into the reviews table with the given order ID
    cursor.execute('''
        INSERT INTO reviews (Order_ID, Rate, Review_Desc)
        VALUES (?, ?, ?)
    ''', (order_id, rate, review_desc))

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
        business_name = get_user_business_name(email, role)
        session['user'] = {
            'email': email,
            'role': role,
            'business_name': business_name
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

#requesting email change
@app.route('/email/change', methods=['POST'])
def email_change_request():
    #make sure user is loged in
    if 'user' not in session:
        return redirect(url_for('mainpage'))

    #get form data
    user_email = session['user']['email']
    new_email = request.form['new_email']
    reason = 'Email change requested'

    #Connect
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #create unique request
    request_id = f"{int(time.time())}{random.randint(1000, 9999)}"

    #insert into request
    cursor.execute('''
        INSERT INTO requests 
        (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request_id, user_email, "helpdeskteam@nittybiz.com", "ChangeID", f"New email: {new_email}\nReason: {reason}", "0"))

    #close
    connection.commit()
    connection.close()

    #go back to profile
    return redirect(url_for('profile', success='Email change request submitted and pending approval'))


# Updated helpdesk_dashboard function to use numeric status values
@app.route('/helpdesk')
def helpdesk_dashboard():
    #make sure user in session is helpdesk
    if 'user' not in session or session['user']['role'] != 'helpdesk':
        return redirect(url_for('mainpage'))

    #access requests
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #get unassigned requests
    cursor.execute('''
        SELECT * FROM requests
        WHERE helpdesk_staff_email = 'helpdeskteam@nittybiz.com'
        AND request_status = '0'
        ORDER BY request_id
    ''')
    unassigned_requests = cursor.fetchall()

    #get requests assigned to current user
    cursor.execute('''
        SELECT * FROM requests
        WHERE helpdesk_staff_email = ?
        ORDER BY request_status, request_id
    ''', (session['user']['email'],))
    assigned_requests = cursor.fetchall()

    #get parent categories if adding new category
    cursor.execute('''
        SELECT DISTINCT parent_category FROM categories
        WHERE parent_category IS NOT NULL
        ORDER BY parent_category
    ''')
    parent_categories = [row[0] for row in cursor.fetchall()]

    connection.close()

    return render_template('helpdesk.html',
                          user=session['user'],
                          unassigned_requests=unassigned_requests,
                          assigned_requests=assigned_requests,
                          parent_categories=parent_categories)

#claim requests
@app.route('/helpdesk/claim', methods=['POST'])
def claim_request():
    #make sure user in session
    if 'user' not in session or session['user']['role'] != 'helpdesk':
        return redirect(url_for('mainpage'))

    #get request id
    request_id = request.form['request_id']

    #connect to db
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #update request when claimed
    cursor.execute('''
        UPDATE requests
        SET helpdesk_staff_email = ?
        WHERE request_id = ?
        AND helpdesk_staff_email = 'helpdeskteam@nittybiz.com'
        AND request_status = '0'
    ''', (session['user']['email'], request_id))

    #close
    connection.commit()
    connection.close()

    #redirect
    return redirect(url_for('helpdesk_dashboard', success=f'Request {request_id} has been assigned to you.'))

#for completed actions
@app.route('/helpdesk/complete', methods=['POST'])
def complete_request():
    #make sure user in session
    if 'user' not in session or session['user']['role'] != 'helpdesk':
        return redirect(url_for('mainpage'))

    #get request id
    request_id = request.form['request_id']

    #connect
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #mark as completed
    cursor.execute('''
        UPDATE requests
        SET request_status = '1'
        WHERE request_id = ? AND helpdesk_staff_email = ?
    ''', (request_id, session['user']['email']))

    #commit and close
    connection.commit()
    connection.close()

    return redirect(url_for('helpdesk_dashboard', success=f'Request {request_id} has been marked as completed.'))

#Adding category
@app.route('/helpdesk/add_category', methods=['POST'])
def add_category():
    #make sure in session
    if 'user' not in session or session['user']['role'] != 'helpdesk':
        return redirect(url_for('mainpage'))

    #get id, category name, and if checkbox is there we know it is a parent
    request_id = request.form['request_id']
    category_name = request.form['category_name']
    is_parent = 'is_parent' in request.form

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #category creation logic
    if is_parent:
        new_parent_name = request.form['new_parent_name']

        cursor.execute('''
            INSERT INTO categories (parent_category, category_name)
            VALUES (?, ?)
        ''', ('Root', new_parent_name))

        if category_name:
            cursor.execute('''
                INSERT INTO categories (parent_category, category_name)
                VALUES (?, ?)
            ''', (new_parent_name, category_name))
    else:
        parent_category = request.form['parent_category']

        cursor.execute('''
            INSERT INTO categories (parent_category, category_name)
            VALUES (?, ?)
        ''', (parent_category, category_name))

    #complete request
    cursor.execute('''
        UPDATE requests
        SET request_status = '1'
        WHERE request_id = ? AND helpdesk_staff_email = ?
    ''', (request_id, session['user']['email']))

    #commit close
    connection.commit()
    connection.close()

    return redirect(url_for('helpdesk_dashboard', success=f'Category "{category_name}" has been added and request {request_id} has been completed.'))


@app.route('/products')
def product_listings():
    #Make sure seller
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    #get email
    user_email = session['user']['email']

    #connect
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #listings
    cursor.execute('''
        SELECT * FROM product_listings
        WHERE Seller_Email = ? AND Status = '1'
        ORDER BY Listing_ID
    ''', (user_email,))
    active_products = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM product_listings
        WHERE Seller_Email = ? AND Status = '0'
        ORDER BY Listing_ID
    ''', (user_email,))
    inactive_products = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM product_listings
        WHERE Seller_Email = ? AND Status = '2'
        ORDER BY Listing_ID
    ''', (user_email,))
    sold_products = cursor.fetchall()

    #get catgories
    cursor.execute('''
        SELECT category_name FROM categories
        ORDER BY category_name
    ''')
    categories = cursor.fetchall()

    #Get reviews
    cursor.execute('''
        SELECT r.Rate, r.Review_Desc, r.Order_ID
        FROM reviews r
        JOIN orders o ON r.Order_ID = o.Order_ID
        WHERE o.Seller_Email = ?
        ORDER BY r.Order_ID DESC
    ''', (user_email,))

    reviews = cursor.fetchall()

    #Get all orders
    cursor.execute('''
        SELECT o.Order_ID, o.Date, o.Buyer_Email, o.Quantity, o.Payment, p.Product_Title
        FROM orders o
        JOIN product_listings p ON o.Listing_ID = p.Listing_ID
        WHERE o.Seller_Email = ?
        ORDER BY o.Date DESC
    ''', (user_email,))

    #get orders
    orders = cursor.fetchall()

    #get  rating
    seller_rating = get_seller_rating(user_email)

    #Dictionaries to map the order id with date and product
    order_products = {}
    order_dates = {}

    for order in orders:
        order_products[order['Order_ID']] = order['Product_Title']
        order_dates[order['Order_ID']] = order['Date']

    connection.close()

    #render with all data
    return render_template('product_listings.html', user=session['user'],active_products=active_products,inactive_products=inactive_products,sold_products=sold_products,categories=categories,reviews=reviews,orders=orders,seller_rating=seller_rating,order_products=order_products,order_dates=order_dates)


#add new product
@app.route('/products/add', methods=['POST'])
def add_product():
    #make sure seller
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    #Get session user
    user_email = session['user']['email']

    #get from form
    category = request.form['category']
    product_title = request.form['product_title']
    product_name = request.form['product_name']
    product_description = request.form['product_description']
    product_price = request.form['product_price']
    quantity = request.form['quantity']

    #product_price = '${product_price}'

    #connect
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #Create unique id for listing
    listing_id = f'{int(time.time())}{random.randint(1000, 9999)}'

    #insert product
    cursor.execute('''
        INSERT INTO product_listings
        (Seller_Email, Listing_ID, Category, Product_Title, Product_Name, Product_Description, Quantity, Product_Price, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '1')
    ''', (user_email, listing_id, category, product_title, product_name, product_description, quantity, product_price))

    #close
    connection.commit()
    connection.close()

    return redirect(url_for('product_listings'))


#requesting new category
@app.route('/request_category', methods=['POST'])
def request_category():
    #make sure is seller
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    #get form data
    user_email = session['user']['email']
    category_name = request.form['category_name']
    parent_category = request.form.get('parent_category', 'Root')
    category_reason = request.form['category_reason']

    #connect
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #create unique id
    request_id = f"{int(time.time())}{random.randint(1000, 9999)}"

    #create description
    request_desc = f"Parent: {parent_category} Category: {category_name}"

    #insert into requests
    cursor.execute('''
        INSERT INTO requests 
        (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request_id, user_email, "helpdeskteam@nittybiz.com", "AddCategory", request_desc, "0"))

    connection.commit()
    connection.close()

    #new category added
    return redirect(url_for('product_listings', success='New category request submitted and pending approval'))

@app.route('/products/update', methods=['POST'])
def update_product():
    #make sure user is seller
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    #get from form.
    user_email = session['user']['email']
    listing_id = request.form['listing_id']
    category = request.form['category']
    product_title = request.form['product_title']
    product_name = request.form['product_name']
    product_description = request.form['product_description']
    product_price = request.form['product_price']
    quantity = request.form['quantity']

    #connect
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    #update
    cursor.execute('''
        UPDATE product_listings
        SET Category = ?, Product_Title = ?, Product_Name = ?, Product_Description = ?, Quantity = ?, Product_Price = ?,
            Status = CASE 
        WHEN ? = 0 THEN '2'
        ELSE Status
        END
        WHERE Listing_ID = ? AND Seller_Email = ?
    ''', (category, product_title, product_name, product_description, quantity, product_price, quantity, listing_id,user_email))

    #close
    connection.commit()
    connection.close()

    return redirect(url_for('product_listings'))


@app.route('/products/deactivate', methods=['POST'])
def deactivate_product():
    #make sure user is seller
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    #Get user and listing id from form
    user_email = session['user']['email']
    listing_id = request.form['listing_id']

    #connecct
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()


    #Get product
    cursor.execute('SELECT Product_Title FROM product_listings WHERE Listing_ID = ? AND Seller_Email = ?',(listing_id, user_email))
    result = cursor.fetchone()

    #product title
    if result:
        product_title = result[0]

    #update listing accordingly
        cursor.execute('''
            UPDATE product_listings
            SET Status = '0'
            WHERE Listing_ID = ? AND Seller_Email = ?
        ''', (listing_id, user_email))

        connection.commit()
        connection.close()

        return redirect(
            url_for('product_listings'))
    else:
        connection.close()
        return redirect(
            url_for('product_listings'))


@app.route('/products/activate', methods=['POST'])
def activate_product():
    #make sure user is seller
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    #get info
    user_email = session['user']['email']
    listing_id = request.form['listing_id']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT Product_Title, Quantity FROM product_listings WHERE Listing_ID = ? AND Seller_Email = ?',
                   (listing_id, user_email))
    result = cursor.fetchone()

    if result:
        product_title, quantity = result

        status = '1' if int(quantity) > 0 else '2'

        cursor.execute('''
            UPDATE product_listings
            SET Status = ?
            WHERE Listing_ID = ? AND Seller_Email = ?
        ''', (status, listing_id, user_email))

        connection.commit()
        connection.close()

        return redirect(url_for('product_listings'))
    else:
        connection.close()
        return redirect(
            url_for('product_listings'))


@app.route('/products/restock', methods=['POST'])
def restock_product():
    if 'user' not in session or session['user']['role'] != 'seller':
        return redirect(url_for('mainpage'))

    user_email = session['user']['email']
    listing_id = request.form['listing_id']
    quantity = request.form['quantity']

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT Product_Title FROM product_listings WHERE Listing_ID = ? AND Seller_Email = ?',
                   (listing_id, user_email))
    result = cursor.fetchone()

    if result:
        product_title = result[0]

        cursor.execute('''
            UPDATE product_listings
            SET Quantity = ?, Status = '1'
            WHERE Listing_ID = ? AND Seller_Email = ?
        ''', (quantity, listing_id, user_email))

        connection.commit()
        connection.close()

        return redirect(
            url_for('product_listings'))
    else:
        connection.close()
        return redirect(
            url_for('product_listings'))

def _open():
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    return c


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    price_min = request.args.get('price_min', '').strip()
    price_max = request.args.get('price_max', '').strip()
    user = session.get('user')

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    sql = '''
        SELECT 
            p.Product_Title, 
            p.Product_Name, 
            p.Category,               -- include category
            p.Product_Description,    -- include description
            s.Business_Name,
            p.Listing_ID, 
            p.Quantity, 
            p.Product_Price, 
            p.Seller_Email
        FROM product_listings p
        JOIN sellers s ON p.Seller_Email = s.email
        WHERE p.Status = 1
    '''
    filters = []
    params = []


    if q:
        filters.append(
            '(p.Product_Title LIKE ? '
            'OR p.Product_Name LIKE ? '
            'OR p.Product_Description LIKE ? '
            'OR p.Category LIKE ? '
            'OR s.Business_Name LIKE ?)'
        )
        like_q = f'%{q}%'
        # five placeholders, one for each field
        params += [like_q, like_q, like_q, like_q, like_q]

    if price_min:
        filters.append(
            "CAST(REPLACE(REPLACE(p.Product_Price, '$', ''), ',', '') AS REAL) >= ?"
        )
        params.append(price_min)


    if price_max:
        filters.append(
            "CAST(REPLACE(REPLACE(p.Product_Price, '$', ''), ',', '') AS REAL) <= ?"
        )
        params.append(price_max)

    if filters:
        sql += ' AND ' + ' AND '.join(filters)

    sql += ' ORDER BY p.Listing_ID'
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()

    enhanced = []
    for title, name, category, description, biz, lid, qty, price, email in rows:
        rating = get_seller_rating(email)
        enhanced.append((title, name, biz, lid, qty, price, email, rating))

    return render_template(
        'mainpage.html',
        listings=enhanced,
        categories=[],
        category="Search Results",
        subcategory="",
        subsubcategory="",
        page=1,
        total_pages=1,
        user=user
    )

if __name__ == '__main__':
    app.run(debug=True)


