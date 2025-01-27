from psycopg2 import pool
from functools import wraps
from os import getenv
from dotenv import load_dotenv

class Connection:
    def __init__(self, user, password, host, port, database):
        self.pool = pool.SimpleConnectionPool(
            minconn=2, maxconn=20, user=getenv("USER"), password=getenv("PASSWORD"),
            host=getenv("HOST"), port=getenv("PORT"), database=getenv("DATABASE"))


    def with_conn(self, func):
        @wraps(func)
        def get_conn(*args, **kwargs):
            connection = self.pool.getconn()
            try:
                result = func(connection, *args, **kwargs)
            finally:
                self.pool.putconn(connection)
            return result
            
        return get_conn


load_dotenv()

