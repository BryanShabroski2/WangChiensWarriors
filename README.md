# WangChiensWarriors - Nittany Business

## Overview

NittanyBusiness is a Flask-based web marketplace platform where buyers, sellers, and helpdesk staff can interact. Core features include:

* User registration and authentication with role-based access control

* Product listing management for sellers (add, update, activate/deactivate, restock)

* Browsing and keyword/price-range search across multiple fields

* Category and subcategory navigation with recursive descendant lookup

* Order placement with inventory checks and payment recording

* Seller rating aggregation and review display

* Helpdesk portal for support request handling and category management



## Project Structure

```plaintext
.
├── app.py                 # Main Flask application and routing
├── population.py          # Database population script
├── WCW.sqlite             # SQLite database file
├── dataSet/               # CSV files used to create/populate the database
│   ├── Address.csv
│   ├── Buyers.csv
│   ├── Categories.csv
│   ├── Credit_Cards.csv
│   ├── Helpdesk.csv
│   ├── Orders.csv
│   ├── Product_Listings.csv
│   ├── Requests.csv
│   ├── Reviews.csv
│   ├── Sellers.csv
│   ├── Users.csv
│   └── Zipcode_Info.csv
├── templates/             # HTML templates
│   ├── Publish.html
│   ├── edit.html
│   ├── helpdesk.html
│   ├── listing.html
│   ├── login.html
│   ├── mainpage.html
│   ├── manage.html
│   ├── old_index.html
│   ├── order_review.html
│   ├── product.html
│   ├── product_listings.html
│   ├── profile.html
│   ├── register.html
│   ├── search.html
│   ├── seller.html
│   └── success.html
└── README.md              # This documentation file

```

## Module Descriptions

### app.py

**Flask setup**: creates app, configures secret key, and sets db_path.

**Authentication**: user registration, login/logout, password hashing, and role detection (get_user_role).

**User profile**: view and update profile fields for buyers, sellers, and helpdesk roles.

**Product catalog**:

* mainpage view: paginated listing, category/subcategory/subsubcategory filtering via recursive DFS (dfs_category).

* listing_detail view: detailed product and seller info.

* Template rendering with Bootstrap UI in templates/mainpage.html.

**Search**: /search route supports keyword search across title, name, description, category, business name and price-range filters.

**Order flow**:

* order_review view: shows product details and saved payment methods.

* place_order action: generates unique order IDs, updates inventory, computes payment, and updates seller balance.

**Seller dashboard**:

* /products route: lists active/inactive/sold products.

* management operations (add_product, update_product, activate, deactivate, restock).

**Helpdesk portal**:

* Listing and claiming support requests.

* Completing requests and adding new categories.

### population.py

Script to create and populate all database tables from CSV files under dataSet/.

Uses SQLite and werkzeug.security.generate_password_hash for user passwords.

## Features

### Authentication & Authorization

* Secure user registration and login with hashed passwords

* Role-based access (Buyer, Seller, Helpdesk) for tailored dashboards and actions

* Password change and email update workflows with validation

### Product Catalog & Categories

* Category hierarchy with unlimited depth, navigable via links

* Recursive DFS category filtering to show all subcategory listings

* Paginated product listing (configurable page size, default 60)

* Detailed product page with description, price, quantity, and seller profile link

### Search & Filtering

* Full-text keyword search across Product Title, Product Name, Description, Category, and Seller Business Name

* Price-range filter inputs for minimum and maximum values

* Combined keyword + price filters for precise result narrowing

* Dropdown component to change price inputs without cluttering main search bar

### Order Processing

* Order review page showing product details and saved credit cards

* Unique numeric order ID generation to avoid collisions

* Inventory validation: prevents ordering more than available stock

* Automatic inventory decrement and status update (sold out triggers deactivation)

* Payment calculation and seller balance increment on successful orders

### Seller Dashboard

* Add new products with auto-generated IDs, initial quantity, status, and category selection

* Update product details (title, description, price, quantity) with stock-based status logic

* Activate/deactivate listings and restock out-of-stock items

* View active, inactive, and sold product lists in separate tabs

### Reviews & Ratings

* Buyers submit ratings and textual reviews tied to specific orders

* Seller average rating computation using joined reviews and orders tables

* Display of seller rating on product listings and seller profile pages

### Helpdesk Portal

* Dashboard for viewing unassigned and user-assigned support requests

* Claim requests to take ownership or mark as completed

* Add new parent and child categories directly from request details

* Filter and sort requests by status and assignment for efficient handling


**Functions**:

populateUsers, populateBuyers, populateSellers, populateCategories, populateCreditCards, populateHelpdesk, populateOrders, populateProductListings, populateRequests, populateReviews, populateZipcodeInfo.

**Usage**: run python population.py to regenerate WCW.sqlite from the CSV dataset.

## Requirements

Python 3.x

Flask

Werkzeug

sqlite3

datetime

random

## How to setup

1. Clone the repository

2. Create a Python virtual environment

3. Install dependencies

4. Populate the database:

This reads CSVs from dataSet/ and creates/overwrites WCW.sqlite.

5. Run the Flask app

Visit http://127.0.0.1:5000/ to access the application.


## Configuration

**Database path**: update db_path in app.py if needed.

**Secret key**: change app.secret_key for production use.

**Pagination size**: modify PAGE_SIZE in the mainpage view.

