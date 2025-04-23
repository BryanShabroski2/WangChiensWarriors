#Author: Bryan Luke Shabroski
#Purpose: Use SQLITE to populate database.
import csv
import sqlite3
from werkzeug.security import generate_password_hash


#IMPORTANT----------------------------------------------------------------
#This function is like every single one, so I am only documenting this one.
def populateUsers(usersCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL
        )
    ''')

    connection.commit()

    #Open the CSV and change the password into a hashed password
    #Then we insert into the connected database
    with open(usersCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row['email']
            unhashedPassword = row['password']
            hashed = generate_password_hash(unhashedPassword)
            cursor.execute(
                'INSERT  INTO users (email, hashed_password) VALUES (?, ?)',(email, hashed)
            )
            print("Populated user with email '{}'".format(email))
    connection.commit()
    connection.close()
    print('Users populated.')


def populateBuyers(buyersCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyers (
            email TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            buyer_address_id TEXT NOT NULL
        )
    ''')

    with open(buyersCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row['email']
            business_name = row['business_name']
            buyer_address_id = row['buyer_address_id']

            cursor.execute(
                'INSERT INTO buyers (email, business_name, buyer_address_id) VALUES (?, ?, ?)',
                (email, business_name, buyer_address_id)
            )
            print("Populated buyer with email '{}'".format(email))
    connection.commit()
    connection.close()
    print('Buyers populated.')


def populateSellers(sellersCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            email TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            Business_Address_ID TEXT NOT NULL,
            bank_routing_number TEXT NOT NULL,
            bank_account_number TEXT NOT NULL,
            balance REAL NOT NULL
        )
    ''')

    with open(sellersCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row['email']
            business_name = row['business_name']
            business_address_id = row['Business_Address_ID']
            bank_routing_number = row['bank_routing_number']
            bank_account_number = row['bank_account_number']
            balance = row['balance']

            cursor.execute(
                'INSERT INTO sellers (email, business_name, Business_Address_ID, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?, ?, ?)',
                (email, business_name, business_address_id, bank_routing_number, bank_account_number, balance)
            )
            print("Populated seller with email '{}'".format(email))
    connection.commit()
    connection.close()
    print('Sellers populated.')


def populateCategories(categoriesCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            parent_category TEXT,
            category_name TEXT PRIMARY KEY
        )
    ''')

    with open(categoriesCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            parent_category = row['parent_category']
            category_name = row['category_name']

            cursor.execute(
                'INSERT INTO categories (parent_category, category_name) VALUES (?, ?)',
                (parent_category, category_name)
            )
            print("Populated category '{}'".format(category_name))
    connection.commit()
    connection.close()
    print('Categories populated.')


def populateCreditCards(creditCardsCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_cards (
            credit_card_num TEXT PRIMARY KEY,
            card_type TEXT NOT NULL,
            expire_month INTEGER NOT NULL,
            expire_year INTEGER NOT NULL,
            security_code TEXT NOT NULL,
            Owner_email TEXT NOT NULL
        )
    ''')

    with open(creditCardsCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            credit_card_num = row['credit_card_num']
            card_type = row['card_type']
            expire_month = row['expire_month']
            expire_year = row['expire_year']
            security_code = row['security_code']
            owner_email = row['Owner_email']

            cursor.execute(
                'INSERT INTO credit_cards (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email) VALUES (?, ?, ?, ?, ?, ?)',
                (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email)
            )
            print("Populated credit card for owner '{}'".format(owner_email))
    connection.commit()
    connection.close()
    print('Credit cards populated.')


def populateHelpdesk(helpdeskCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS helpdesk (
            email TEXT PRIMARY KEY,
            Position TEXT NOT NULL
        )
    ''')

    with open(helpdeskCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row['email']
            position = row['Position']

            cursor.execute(
                'INSERT INTO helpdesk (email, Position) VALUES (?, ?)',
                (email, position)
            )
            print("Populated helpdesk staff with email '{}'".format(email))
    connection.commit()
    connection.close()
    print('Helpdesk staff populated.')


def populateOrders(ordersCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            Order_ID TEXT PRIMARY KEY,
            Seller_Email TEXT NOT NULL,
            Listing_ID TEXT NOT NULL,
            Buyer_Email TEXT NOT NULL,
            Date TEXT NOT NULL,
            Quantity INTEGER NOT NULL,
            Payment REAL NOT NULL
        )
    ''')

    with open(ordersCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            order_id = row['Order_ID']
            seller_email = row['Seller_Email']
            listing_id = row['Listing_ID']
            buyer_email = row['Buyer_Email']
            date = row['Date']
            quantity = row['Quantity']
            payment = row['Payment']

            cursor.execute(
                'INSERT INTO orders (Order_ID, Seller_Email, Listing_ID, Buyer_Email, Date, Quantity, Payment) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (order_id, seller_email, listing_id, buyer_email, date, quantity, payment)
            )
            print("Populated order with ID '{}'".format(order_id))
    connection.commit()
    connection.close()
    print('Orders populated.')


def populateProductListings(productListingsCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_listings (
            Seller_Email TEXT NOT NULL,
            Listing_ID TEXT PRIMARY KEY,
            Category TEXT NOT NULL,
            Product_Title TEXT NOT NULL,
            Product_Name TEXT NOT NULL,
            Product_Description TEXT NOT NULL,
            Quantity INTEGER NOT NULL,
            Product_Price REAL NOT NULL,
            Status TEXT NOT NULL
        )
    ''')

    with open(productListingsCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            seller_email = row['Seller_Email']
            listing_id = row['Listing_ID']
            category = row['Category']
            product_title = row['Product_Title']
            product_name = row['Product_Name']
            product_description = row['Product_Description']
            quantity = row['Quantity']
            product_price = row['Product_Price']
            status = row['Status']

            cursor.execute(
                'INSERT INTO product_listings (Seller_Email, Listing_ID, Category, Product_Title, Product_Name, Product_Description, Quantity, Product_Price, Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (seller_email, listing_id, category, product_title, product_name, product_description, quantity,
                 product_price, status)
            )
            print("Populated product listing with ID '{}'".format(listing_id))
    connection.commit()
    connection.close()
    print('Product listings populated.')


def populateRequests(requestsCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            sender_email TEXT NOT NULL,
            helpdesk_staff_email TEXT,
            request_type TEXT NOT NULL,
            request_desc TEXT NOT NULL,
            request_status TEXT NOT NULL
        )
    ''')

    with open(requestsCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            request_id = row['request_id']
            sender_email = row['sender_email']
            helpdesk_staff_email = row['helpdesk_staff_email']
            request_type = row['request_type']
            request_desc = row['request_desc']
            request_status = row['request_status']

            cursor.execute(
                'INSERT INTO requests (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) VALUES (?, ?, ?, ?, ?, ?)',
                (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status)
            )
            print("Populated request with ID '{}'".format(request_id))
    connection.commit()
    connection.close()
    print('Requests populated.')


def populateReviews(reviewsCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            Order_ID TEXT PRIMARY KEY,
            Rate INTEGER NOT NULL,
            Review_Desc TEXT NOT NULL
        )
    ''')

    with open(reviewsCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            order_id = row['Order_ID']
            rate = row['Rate']
            review_desc = row['Review_Desc']

            cursor.execute(
                'INSERT INTO reviews (Order_ID, Rate, Review_Desc) VALUES (?, ?, ?)',
                (order_id, rate, review_desc)
            )
            print("Populated review for order '{}'".format(order_id))
    connection.commit()
    connection.close()
    print('Reviews populated.')


def populateZipcodeInfo(zipcodeInfoCsvPath, dbPath):
    connection = sqlite3.connect(dbPath)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zipcode_info (
            zipcode TEXT PRIMARY KEY,
            city TEXT NOT NULL,
            state TEXT NOT NULL
        )
    ''')

    with open(zipcodeInfoCsvPath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zipcode = row['zipcode']
            city = row['city']
            state = row['state']

            cursor.execute(
                'INSERT INTO zipcode_info (zipcode, city, state) VALUES (?, ?, ?)',
                (zipcode, city, state)
            )
            print("Populated zipcode '{}'".format(zipcode))
    connection.commit()
    connection.close()
    print('Zipcode info populated.')

#In our main, we set the paths to our CSV's and database. Then we call the respective functions.
if __name__ == '__main__':
    UsersCsvPath = 'dataSet/Users.csv'
    BuyersCsvPath = 'dataSet/Buyers.csv'
    SellersCsvPath = 'dataSet/Sellers.csv'
    CategoriesCsvPath = 'dataSet/Categories.csv'
    CreditCardsCsvPath = 'dataSet/Credit_Cards.csv'
    HelpdeskCsvPath = 'dataSet/Helpdesk.csv'
    OrdersCsvPath = 'dataSet/Orders.csv'
    ProductListingsCsvPath = 'dataSet/Product_Listings.csv'
    RequestsCsvPath = 'dataSet/Requests.csv'
    ReviewsCsvPath = 'dataSet/Reviews.csv'
    ZipcodeCsvPath = 'dataSet/Zipcode_Info.csv'
    dbPath = 'WCW.sqlite'

    populateUsers(UsersCsvPath, dbPath)
    populateBuyers(BuyersCsvPath, dbPath)
    populateSellers(SellersCsvPath, dbPath)
    populateCategories(CategoriesCsvPath, dbPath)
    populateCreditCards(CreditCardsCsvPath, dbPath)
    populateHelpdesk(HelpdeskCsvPath, dbPath)
    populateOrders(OrdersCsvPath, dbPath)
    populateProductListings(ProductListingsCsvPath, dbPath)
    populateRequests(RequestsCsvPath, dbPath)
    populateReviews(ReviewsCsvPath, dbPath)
    populateZipcodeInfo(ZipcodeCsvPath, dbPath)