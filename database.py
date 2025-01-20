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

user = getenv('USER')
password = getenv('PASSWORD')
host = getenv('HOST')
port = getenv('PORT')
database = getenv('DATABASE')

db_conn = Connection(user=user, password=password, host=host, port=port, database=database)

@db_conn.with_conn
def fetch_test(conn : connection):
    cursor = conn.cursor()
    query = "SELECT * FROM test"
    cursor.execute(query)
    result = cursor.fetchall()
    print(result)
    
if __name__ == "__main__":
    fetch_test()