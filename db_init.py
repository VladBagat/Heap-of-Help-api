from psycopg2 import pool
from functools import wraps

class Connection:
    def __init__(self, user, password, host, port, database):
        self.pool = pool.SimpleConnectionPool(
            minconn=2, maxconn=20, user=user, password=password, 
            host=host, port=port, database=database)

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


    
    