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
from psycopg2.extras import execute_values
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
def messages_table_setup(con: connection):
    with con.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS messages (
            id serial PRIMARY KEY,
            sender varchar (150) NOT NULL REFERENCES users(username)
            ON DELETE CASCADE ON UPDATE CASCADE,
            recipient varchar (150) NOT NULL REFERENCES users(username)
            ON DELETE CASCADE ON UPDATE CASCADE,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT NOW(),
            CONSTRAINT sender_recipient_check CHECK (sender <> recipient)
        )""")
        
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
def fetch_item_tags(conn : connection):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM item_tags ORDER BY RANDOM() LIMIT 100;"))
        return cur.fetchall()

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
def get_tutor_profile(con : connection):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            'SELECT first_name, last_name, description, profile_img FROM tutors WHERE tutor_id={tutor_id};'
            ).format(
            tutor_id=sql.Literal(1),
            ))
        tutor_data = cur.fetchone()
        if tutor_data:
            return {
                "first_name": tutor_data[0],
                "last_name": tutor_data[1],
                "description": tutor_data[2],
                "profile_img": base64.b64encode(tutor_data[3]).decode('utf-8')  # This is in BYTEA format
            }
        else:
            return None  # No data found

@db_conn.with_conn

def is_tutor(con : connection, request_username):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            "SELECT id FROM users WHERE username={username};"
            ).format(
            username=sql.Literal(request_username),
            ))
        user_id = cur.fetchone()
        cur.execute(sql.SQL(
            "SELECT tutor_id FROM tutors WHERE id={id};"
            ).format(
            id=sql.Literal(user_id),
            ))
        tutor_id = cur.fetchone()
        if tutor_id is None:
            return False
        else:
            return True

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
    
@db_conn.with_conn 
def store_message(con : connection, sender: str, recipient: str, content: str):
    with con.cursor() as cur:
        cur.execute(sql.SQL("""INSERT INTO messages (sender, recipient, content)
                    VALUES ({sender}, {recipient}, {content})""")
                    .format(sender=sql.Literal(sender),
                            recipient = sql.Literal(recipient),
                            content = sql.Literal(content)))
    con.commit()

@db_conn.with_conn 
def fetch_messages(con : connection, sender: str, recipient: str):
    with con.cursor() as cur:
        cur.execute(sql.SQL("""SELECT content FROM messages
                    WHERE sender={sender} AND recipient={recipient}
                    ORDER BY timestamp DESC LIMIT 50""")
                    .format(sender=sql.Literal(sender),
                            recipient = sql.Literal(recipient)))
        return cur.fetchall()
@db_conn.with_conn
def fetch_user_chats(con : connection, userid: str):
    with con.cursor() as cur:
        cur.execute(sql.SQL("""SELECT
    CASE
        WHEN sender = :{userID} THEN sender
        ELSE recipient
    END AS {user_id}
FROM messages
WHERE sender = :{userID} OR recipient = :{userID};
        """).format(userID=sql.Literal(userid)))
    return cur.fetchall()

@db_conn.with_conn
def fetch_test(conn : connection):
    with conn.cursor() as cursor:
        query = "SELECT * FROM users;"
        cursor.execute(query)
        result = cursor.fetchall()

if __name__ == "__main__":
    fetch_test()
    