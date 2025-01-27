'''I assume this module to be a collection of all database methods so it will looks cleaner. 
I.e. main.py is for endpoints; database.py for db method.
This is definitely arguable.'''

'''
Start functions with `@db_conn.with_conn`. This handles getting and putting connections for you. 
We have at most 20 connections! Consult db_init.py for details.
'''

from os import getenv
from db_init import Connection
from psycopg2.extensions import connection
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

user = getenv('USER')
password = getenv('PASSWORD')
host = getenv('HOST')
port = getenv('PORT')
database = getenv('DATABASE')

db_conn = Connection(user=user, password=password, host=host, port=port, database=database)

@db_conn.with_conn
def users_table_setup(con : connection):
    with con.cursor() as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY,'
                    'username varchar (150) NOT NULL,'
                    'password TEXT NOT NULL,'
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
                    )
        cur.execute("INSERT INTO users (username, password) "
                    "VALUES ('TEST', 'test');")
        con.commit()
       
@db_conn.with_conn 
def register_user_db(con : connection, request_username, hashed_password):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            "INSERT INTO users (username, password) VALUES ({username}, {password});"
        ).format(
            username=sql.Literal(request_username),
            password=sql.Literal(hashed_password)
        ))
        
        con.commit()

@db_conn.with_conn
def fetch_test(conn : connection):
    with conn.cursor() as cursor:
        query = "SELECT * FROM test"
        cursor.execute(query)
        result = cursor.fetchall()
        print(result)

if __name__ == "__main__":
    fetch_test()