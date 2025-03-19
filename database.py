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

user = getenv('USER_db')
password = getenv('PASSWORD')
host = getenv('HOST')
database = getenv('DATABASE')


db_conn = Connection(user=user, password=password, host=host, database=database)

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

@db_conn.with_conn 
def can_get_rated(con: connection, tutor_id, user_id):
    with con.cursor() as cur:
        #check if the user(tutee) sent at least 1 message to tutor
        cur.execute("""
            SELECT COUNT() FROM messages
            WHERE sender_id = %s AND recipient_id = %s
        """, (user_id, tutor_id))
        user_to_tutor_msg_count = cur.fetchone()[0]

        #check if the tutor has sent at least 1 message to user
        cur.execute("""
            SELECT COUNT() FROM messages
            WHERE sender_id = %s AND recipient_id = %s
        """, (tutor_id, user_id))
        tutor_to_user_msg_count = cur.fetchone()[0]


        if user_to_tutor_msg_count > 0 and tutor_to_user_msg_count > 0:
            return True
        else:
            return False
        
if __name__ == "__main__":
    fetch_test()
