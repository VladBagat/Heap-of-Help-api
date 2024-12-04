from functools import wraps
from flask import request, abort
import jwt
from os import getenv

jwt_secret = getenv('SECRET')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt')
        
        if not token:
            abort(401, description="Authorization token is missing")
        try:
            data=jwt.decode(token, jwt_secret, algorithms=["HS256"])
            current_user=data["user_id"]
            if current_user is None:
                abort(403, description="Bad Credentials")
        except jwt.ExpiredSignatureError:
            abort(403, description="Token is outdated")

        return f(current_user, *args, **kwargs)

    return decorated