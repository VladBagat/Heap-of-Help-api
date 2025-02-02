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
from psycopg2.extras import execute_values
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
def tags_table_setup(con : connection):
    """Creates user_tags and item_tags tables"""
    with con.cursor() as cur:
        
        user_tags = sql.SQL(
            """CREATE TABLE IF NOT EXISTS user_tags 
            (user_tag_id serial PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
            tag1 INT,
            tag2 INT,
            tag3 INT,
            tag4 INT,
            tag5 INT);""")
        item_tags = sql.SQL(
            """CREATE TABLE IF NOT EXISTS item_tags 
            (item_tag_id serial PRIMARY KEY,
            item_id INT NOT NULL REFERENCES items(id) ON DELETE CASCADE ON UPDATE CASCADE,
            tag1 INT,
            tag2 INT,
            tag3 INT,
            tag4 INT,
            tag5 INT);""")
        
        cur.execute(user_tags)
        cur.execute(item_tags)
        con.commit()
        
@db_conn.with_conn
def items_table_setup(con : connection):
    with con.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS items (
            id serial PRIMARY KEY,
            name varchar (150) NOT NULL);""")
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
def fetch_item_tags(conn : connection):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM item_tags ORDER BY RANDOM() LIMIT 100;"))
        return cur.fetchall()


@db_conn.with_conn
def fetch_user_tags(conn : connection, user_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL(
            """SELECT user_tags.tag1,
                user_tags.tag2,
                user_tags.tag3,
                user_tags.tag4,
                user_tags.tag5
            FROM user_tags JOIN users ON user_tags.user_id = users.id
            WHERE users.username = {user_id};"""
        ).format(user_id=sql.Literal(user_id)))
        return cur.fetchall()
    
@db_conn.with_conn 
def fetch_recommended_items(conn : connection, item_id_list : list):
    with conn.cursor() as cur:
        query = """SELECT items.name 
        FROM item_tags JOIN items ON item_tags.item_id = items.id
        WHERE items.id IN %s;"""
        execute_values(cur, query, (tuple(item_id_list),))
        return cur.fetchall()
    