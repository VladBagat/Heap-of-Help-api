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
def fetch_user_tags(conn : connection, user_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL(
            """SELECT tag1, tag2, tag3, tag4, tag5
            FROM tags JOIN users ON tags.user_id = users.id
            WHERE users.username = {user_id};"""
        ).format(user_id=sql.Literal(user_id)))
        return cur.fetchall()

@db_conn.with_conn
def fetch_tutor_tags(conn : connection):
    with conn.cursor() as cur:
        cur.execute('''SELECT t.* FROM tags t
                    JOIN tutors tut ON t.user_id = tut.id
                    ORDER BY RANDOM() LIMIT 100;''')

        return cur.fetchall()
    
@db_conn.with_conn 
def fetch_recommended_tutors(conn : connection, item_id_list : list):
    with conn.cursor() as cur:
        query = """SELECT forename, surname, description, profile_img 
        FROM tutors WHERE id IN %s;"""
        execute_values(cur, query, (tuple(item_id_list),))
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
def register_tutor(con : connection, request_username, hashed_password, 
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

            cur.execute("INSERT INTO tutors (forename, surname, email, age, education, language, timezone, profile_img, description, id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (request_forename, request_surname, request_email, request_age,
             request_education, request_language, request_timezone, binary_img,
             request_description, user_id))

            columns = [f"tag{i+1}" for i in range(len(tag_list))]  # Create column names dynamically
            placeholders = ", ".join(["%s"] * len(tag_list))  # Create %s placeholders dynamically

            sql = f"INSERT INTO tags (user_id, {', '.join(columns)}) VALUES (%s, {placeholders})"

            # Execute with user_id as the first parameter
            cur.execute(sql, (user_id, *tag_list))
            
        except UserExists:
            return False
        else:
            con.commit()
            return True
        
@db_conn.with_conn 
def register_tutee(con : connection, request_username, hashed_password, 
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

            cur.execute("INSERT INTO tutees (forename, surname, email, age, education, language, timezone, profile_img, description, id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (request_forename, request_surname, request_email, request_age,
             request_education, request_language, request_timezone, binary_img,
             request_description, user_id))
            
            columns = [f"tag{i+1}" for i in range(len(tag_list))]  # Create column names dynamically
            placeholders = ", ".join(["%s"] * len(tag_list))  # Create %s placeholders dynamically

            sql = f"INSERT INTO tags (user_id, {', '.join(columns)}) VALUES (%s, {placeholders})"

            # Execute with user_id as the first parameter
            cur.execute(sql, (user_id, *tag_list))

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
        # cur.execute('DROP TABLE tutees;')
        cur.execute('CREATE TABLE IF NOT EXISTS tutees (tutee_id serial PRIMARY KEY,'
                    'forename varchar (150) NOT NULL,'
                    'surname varchar (150) NOT NULL,'
                    'email varchar (255) NOT NULL,'
                    'age INT,'
                    'education TEXT,'
                    'language TEXT,'
                    'timezone TEXT,'
                    'profile_img BYTEA,'
                    'description TEXT,'
                    'id INTEGER REFERENCES users(id) ON DELETE CASCADE);'
                    )
        
        '''
        """Save an image to the database in BYTEA format."""
        with open("default_img.jpg", 'rb') as file:
            binary_data = file.read()  # Read image as binary

        cur.execute("""
        INSERT INTO tutees (first_name, last_name, description, id, profile_img) 
        VALUES (%s, %s, %s, %s, %s)
    """, ("Test", "test", "Hi", 234, binary_data))
        '''
        
        con.commit()
        con.close()
        
@db_conn.with_conn
def tutors_table_setup(con : connection):
    with con.cursor() as cur:
        #cur.execute('DROP TABLE tutors;')
        cur.execute('CREATE TABLE IF NOT EXISTS tutors (tutor_id serial PRIMARY KEY,'
                    'forename varchar (150) NOT NULL,'
                    'surname varchar (150) NOT NULL,'
                    'email varchar (255) NOT NULL,'
                    'age INT,'
                    'education TEXT,'
                    'language TEXT,'
                    'timezone TEXT,'
                    'profile_img BYTEA,'
                    'description TEXT,'
                    'id INTEGER REFERENCES users(id) ON DELETE CASCADE);'
                    )
        
        '''
        """Save an image to the database in BYTEA format."""
        with open("default_img.jpg", 'rb') as file:
            binary_data = file.read()  # Read image as binary

        cur.execute("""
        INSERT INTO tutees (first_name, last_name, description, id, profile_img) 
        VALUES (%s, %s, %s, %s, %s)
    """, ("Test", "test", "Hi", 234, binary_data))
        '''
        
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
def get_tutor_profile(con : connection, tutor_id):
    with con.cursor() as cur:
        cur.execute(sql.SQL(
            'SELECT forename, surname, description, profile_img FROM tutors WHERE tutor_id={tutor_id};'
            ).format(
            tutor_id=sql.Literal(tutor_id),
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

@db_conn.with_conn
def fetch_test(conn : connection):
    with conn.cursor() as cursor:
        query = "SELECT * FROM users;"
        cursor.execute(query)
        result = cursor.fetchall()

if __name__ == "__main__":
    fetch_test()
    