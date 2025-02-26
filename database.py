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

load_dotenv()

user = getenv('USER_db')
password = getenv('PASSWORD')
host = getenv('HOST')
database = getenv('DATABASE')


db_conn = Connection(user=user, password=password, host=host, database=database)

@db_conn.with_conn
def users_table_setup(con : connection):
    with con.cursor() as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS users ('
                    'id SERIAL PRIMARY KEY,'
                    'forename VARCHAR(100) NOT NULL,'
                    'surname VARCHAR(100) NOT NULL,'
                    'email VARCHAR(255) NOT NULL UNIQUE,'
                    'phonenumber VARCHAR(15) NOT NULL,'
                    'password TEXT NOT NULL,'
                    'role VARCHAR(10) CHECK (role IN (\'tutor\', \'tutee\')) NOT NULL,'
                    'profile_image TEXT DEFAULT NULL,'
                    'location VARCHAR(255) DEFAULT NULL,'
                    'description TEXT DEFAULT NULL,'
                    'tags TEXT DEFAULT NULL,'
                    'rating DECIMAL(3,1) DEFAULT NULL,'
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                    ');'
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
def update_user_profile(con: connection, user_id, profile_image, location, description, tags, rating):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            "UPDATE users SET profile_image = {profile_image}, location = {location}, "
            "description = {description}, tags = {tags}, rating = {rating} "
            "WHERE id = {user_id};"
        ).format(
            profile_image=sql.Literal(profile_image),
            location=sql.Literal(location),
            description=sql.Literal(description),
            tags=sql.Literal(tags),
            rating=sql.Literal(rating),
            user_id=sql.Literal(user_id)
        ))
        con.commit()



@db_conn.with_conn
def fetch_test(conn : connection):
    with conn.cursor() as cursor:
        query = "SELECT * FROM users;"
        cursor.execute(query)
        result = cursor.fetchall()

if __name__ == "__main__":
    fetch_test()
