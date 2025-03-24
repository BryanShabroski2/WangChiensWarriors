#Author: Bryan Luke Shabroski
#Purpose: Use SQLITE to populate our Users from csv. Hash the password as we store the
#user. We do this using the library werkzeug.secrurity.
import csv
import sqlite3
from werkzeug.security import generate_password_hash

def populateUsers(csvPath, dbPath):
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
    with open(csvPath, newline='', encoding='utf-8-sig') as csvfile:
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

if __name__ == '__main__':
    csvPath = 'Users.csv'
    dbPath = 'WCW.sqlite'
    populateUsers(csvPath, dbPath)