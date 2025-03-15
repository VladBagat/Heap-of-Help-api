from functools import wraps
from flask import request, abort
import jwt
from os import getenv
import json

jwt_secret = getenv('SECRET')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt')
        
        if not token:
            abort(401, description="Authorization token is missing")
        try:
            data=jwt.decode(token, jwt_secret, algorithms=["HS256"])
            current_user=data["username"]
            user_id = data["user_id"]
            if current_user is None:
                abort(403, description="Bad Credentials")
        except jwt.ExpiredSignatureError:
            abort(403, description="Token is outdated")
        except KeyError: {
            abort(403, description="Bad Credentials")
        }

        return f(current_user, user_id, *args, **kwargs)

    return decorated

def tag_encoder(tag) -> int:
    """Takes a tag string and outputs a unique integer id"""
    with open("lookup.json", "r") as f:
        lookup = json.load(f)
    try:
        return lookup[tag]
    except KeyError:
        raise KeyError("Tag not found in lookup table")

def tag_decoder(tag_id) -> str:
    """Takes an unique integer id and outputs a tag string"""
    with open("lookup.json", "r") as f:
        lookup = json.load(f)
    try:
        return list(lookup.keys())[list(lookup.values()).index(tag_id)]
    except KeyError:
        raise KeyError("Tag not found in lookup table")

    