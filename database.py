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
            """CREATE TABLE IF NOT EXISTS tags 
            (tag_id serial PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
            tag1 INT,
            tag2 INT,
            tag3 INT,
            tag4 INT,
            tag5 INT);""")
        
        cur.execute(user_tags)
    con.commit()

@db_conn.with_conn
def fetch_user_tags(conn: connection, user_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL(
            """SELECT tag1, tag2, tag3, tag4, tag5
            FROM tags JOIN users ON tags.user_id = users.id
            WHERE users.id = {user_id};"""
        ).format(user_id=sql.Literal(user_id)))
        return cur.fetchall()

@db_conn.with_conn
def fetch_tutor_tags(conn: connection, ignore_profiles_list):
    if not ignore_profiles_list:
        ignore_profiles_list = [-1]
    with conn.cursor() as cur:
        cur.execute('''SELECT t.* FROM tags t
               JOIN profiles p ON t.user_id = p.id
               WHERE p.discoverable = true
               AND p.id NOT IN %s
               ORDER BY RANDOM() 
               LIMIT 100;''', (tuple(ignore_profiles_list),))

        return cur.fetchall()
    
@db_conn.with_conn 
def fetch_recommended_tutors(conn: connection, item_id_list: list):
    with conn.cursor() as cur:
        # Include id in the SELECT statement
        query = """SELECT id, forename, surname, description, profile_img 
        FROM profiles WHERE id IN %s;"""
        cur.execute(query, (tuple(item_id_list),))
        return cur.fetchall()
        
@db_conn.with_conn 
def validate_username(con : connection, request_username):
    with con.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username=%s;", (request_username,))
        user_id = cur.fetchone()
        if user_id == None:
            return True
        else:
            return False

       
@db_conn.with_conn 
def register_profile(con: connection, request_profile, request_username, hashed_password, 
                   request_forename, request_surname, request_email, request_age,
                   request_language, request_timezone, request_description,
                   request_education, request_profile_img, tag_list):
    with con.cursor() as cur:
        # Error for Unique field violation
        UserExists = errors.lookup('23505')
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id;",
            (request_username, hashed_password))
            user_id = cur.fetchone()[0]  # Get the user ID directly
            if request_profile_img:
                binary_img = base64.b64decode(request_profile_img.split(",")[1])  # Decode Base64
            else:
                with open("default_img.jpg", "rb") as file:
                    binary_img = file.read()  # Default image
            cur.execute("INSERT INTO profiles (forename, surname, email, age, education, language, timezone, profile_img, description, id, discoverable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (request_forename, request_surname, request_email, request_age,
             request_education, request_language, request_timezone, binary_img,
             request_description, user_id, request_profile))
            
            columns = [f"tag{i+1}" for i in range(len(tag_list))]  # Create column names dynamically
            placeholders = ", ".join(["%s"] * len(tag_list))  # Create %s placeholders dynamically

            sql = f"INSERT INTO tags (user_id, {', '.join(columns)}) VALUES (%s, {placeholders})"

            # Execute with user_id as the first parameter
            cur.execute(sql, (user_id, *tag_list))

        except UserExists:
            return None
        else:
            con.commit()
            return user_id


@db_conn.with_conn
def login_user_db(con: connection, request_username, request_password):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            "SELECT password, id FROM users WHERE username={username};"
            ).format(
            username=sql.Literal(request_username),
            ))

        hashed_pass, id = cur.fetchone()
        if hashed_pass is None:
            return False
        if bcrypt.checkpw(request_password.encode('utf-8'),
                          hashed_pass.encode('utf-8')):
            return id
        return False
       
@db_conn.with_conn
def profiles_table_setup(con: connection):
    with con.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS profiles (
            profile_id serial PRIMARY KEY,
            id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            discoverable BOOLEAN NOT NULL,
            forename varchar (150) NOT NULL,
            surname varchar (150) NOT NULL,
            email varchar (255) NOT NULL,
            age INT,
            education TEXT,
            language TEXT,
            timezone TEXT,
            profile_img BYTEA,
            description TEXT)
            ;'''
            )
    con.commit()
               
@db_conn.with_conn
def get_profile(con, user_id):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            '''SELECT forename, surname, email, age, education, language, timezone, description, profile_img
               FROM profiles WHERE id={user_id};'''
        ).format(user_id=sql.Literal(user_id)))
        
        user_data = cur.fetchone()
        
        if user_data:
            return {
                "forename": user_data[0], 
                "surname": user_data[1],
                "email": user_data[2],
                "age": user_data[3],
                "education": user_data[4],
                "language": user_data[5],
                "timezone": user_data[6],
                "description": user_data[7],
                "profile_img": base64.b64encode(user_data[8]).decode('utf-8') if user_data[8] else None
            }
        else:
            return None

@db_conn.with_conn
def is_tutor(con: connection, user_id):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            "SELECT discoverable FROM profiles WHERE id={user_id};"
            ).format(
            user_id=sql.Literal(user_id),
            ))
        discoverable = cur.fetchone()
        if discoverable:
            return True
        else:
            return False

@db_conn.with_conn
def update_profile_db(con: connection, user_id, forename, surname, email, age, education, language, timezone, description):
    with con.cursor() as cur:
        try:
            cur.execute("""
                UPDATE profiles
                SET forename = %s, surname = %s, email = %s, age = %s, 
                    education = %s, language = %s, timezone = %s, description = %s
                WHERE id = %s;
            """, (forename, surname, email, age, education, language, timezone, description, user_id))
            con.commit()
            return True
        except Exception as e:
            print("Database update error:", e)
            return False
