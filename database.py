'''I assume this module to be a collection of all database methods so it will looks cleaner. 
I.e. main.py is for endpoints; database.py for db method.
This is definitely arguable.'''
import bcrypt

'''
Start functions with `@db_conn.with_conn`. This handles getting and putting connections for you. 
We have at most 20 connections! Consult db_init.py for details.
'''

from os import getenv
from db_init import Connection
from psycopg2.extensions import connection
from psycopg2 import sql, errors
from dotenv import load_dotenv
import base64

load_dotenv()

user = getenv('USER_db')
password = getenv('PASSWORD')
host = getenv('HOST')
database = getenv('DATABASE')


db_conn = Connection(user=user, password=password, host=host, database=database)

@db_conn.with_conn
def users_table_setup(con : connection):
    with con.cursor() as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY,'
                    'username varchar (150) NOT NULL UNIQUE,'
                    'password TEXT NOT NULL,'
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
                    )
        cur.execute("INSERT INTO users (username, password) "
                    "VALUES ('TEST', 'test');")
        con.commit()


@db_conn.with_conn 
def register_user_db(con : connection, request_username, hashed_password):
    with con.cursor() as cur:
        # Error for Unique field violation
        UserExists = errors.lookup('23505')
        try:
            cur.execute(sql.SQL(
                "INSERT INTO users (username, password) VALUES ({username}, {password});"
            ).format(
                username=sql.Literal(request_username),
                password=sql.Literal(hashed_password)
            ))
        except UserExists:
            return False
        else:
            con.commit()
            return True


@db_conn.with_conn
def login_user_db(con: connection, request_username, request_password):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            "SELECT password FROM users WHERE username={username};"
            ).format(
            username=sql.Literal(request_username),
            ))

        hashed_pass = cur.fetchone()
        if hashed_pass is None:
            return 404
        if bcrypt.checkpw(request_password.encode('utf-8'),
                          hashed_pass[0].encode('utf-8')):
            return 200
        return 401

@db_conn.with_conn
def tutees_table_setup(con : connection):
    with con.cursor() as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS tutees (tutee_id serial PRIMARY KEY,'
                    'first_name varchar (150) NOT NULL,'
                    'last_name varchar (150) NOT NULL,'
                    'description TEXT NOT NULL,'
                    'id INTEGER REFERENCES users(id) ON DELETE CASCADE,'
                    'profile_img BYTEA);'
                    )
        
        """Save an image to the database in BYTEA format."""
        with open("default_img.jpg", 'rb') as file:
            binary_data = file.read()  # Read image as binary

        cur.execute("""
        INSERT INTO tutees (first_name, last_name, description, id, profile_img) 
        VALUES (%s, %s, %s, %s, %s)
    """, ("Test", "test", "Hi", 234, binary_data))
        
        con.commit()
        con.close()
        
@db_conn.with_conn
def get_tutee_profile(con : connection):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            'SELECT first_name, last_name, description, profile_img FROM tutees WHERE tutee_id={tutee_id};'
            ).format(
            tutee_id=sql.Literal(34),
            ))
        tutee_data = cur.fetchone()
        if tutee_data:
            return {
                "first_name": tutee_data[0],
                "last_name": tutee_data[1],
                "description": tutee_data[2],
                "profile_img": base64.b64encode(tutee_data[3]).decode('utf-8')  # This is in BYTEA format
            }
        else:
            return None  # No data found

@db_conn.with_conn
def fetch_test(conn : connection):
    with conn.cursor() as cursor:
        query = "SELECT * FROM users;"
        cursor.execute(query)
        result = cursor.fetchall()

if __name__ == "__main__":
    fetch_test()
