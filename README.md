# WangChiensWarriors - Nittany Business

## Project Structure

```plaintext
.
├── app.py             # Main Flask app file
├── populateUsers.py   # Script to import user data from CSV, hashing passwords
├── Users.csv          # Example CSV file with user data
├── WCW.sqlite         # SQLite database file (stores user information)
├── index.html         # Front-end login page
├── success.html       # Page displayed upon successful login
└── README.md          # Project documentation (this file)


```

## Features

#### **1. User Data Import**

  populateUsers.py reads from Users.csv, hashes passwords, and inserts records into WCW.sqlite.
  
#### **2. Backend Service (Flask)**

app.py provides two basic routes:

* index.html (login page).

* success.html.(login success page)

#### **3.Front-End Demo**

A basic HTML form in index.html allows a user to log in.

## Requirements

Python 3.x

Flask

Werkzeug

## How to setup

**1. Clone or Download**

Make sure the following files are present together:
* app.py

* populateUsers.py

* Users.csv

* WCW.sqlite

* index.html

* success.html

**2. install required packages**
* Flask

* Werkzeug

**3. Import User Data**

populate the database with user data (from Users.csv)
If successful, you should see output like:
```plaintext
Populated user with email 'example@example.com'
Users populated.
```

**4. Run the Flask App**

Start the Flask development server.

By default, Flask will run on http://127.0.0.1:5000. You should see output like:
```plaintext
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## Running in PyCharm

1. Open the Project: In PyCharm, go to File > Open... and select this project's folder.
2. Set Interpreter: Under File > Settings > Project: [project_name] > Python Interpreter
3. Install Dependencies: If necessary, install Flask and Werkzeug via PyCharm’s interface or terminal.
4. Run: Right-click on app.py -> Run 'app'. PyCharm will start the app on port 5000 by default.



## Contact

Author: 

Email: 

GitHub: 
