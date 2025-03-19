from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from os import getenv

from database import register_user_db
from utils import token_required
import re
import bcrypt

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["https://heap-of-help.vercel.app", "http://localhost:5173"]}})

load_dotenv()

jwt_secret = getenv('SECRET')

def generate_jwt(payload):
    return jwt.encode(
        payload, 
        jwt_secret, 
        algorithm="HS256"
    )
    
def generate_cookie(response, token, remember):
    if remember:
        expires = datetime.now(UTC) + timedelta(days=14)
    else:
        expires = None
    
    response.set_cookie(
        "jwt", 
        token, 
        httponly=True, 
        secure=True, 
        samesite="None", #TODO: Evaluate effect of this on security. 
        expires=expires
        )
    
    return response


@app.route("/hello", methods=['GET'])
@token_required
def hello_world(current_user):
    return "<p>Hello, World!</p>"

@app.route("/pageowner", methods=['POST'])
@token_required
def check_owner(current_user):
    if current_user == request.json.get('username'):
        response = make_response(jsonify({
            "success": True,
            "message": "User is owner"}, 200
    ))

    else:
        response = make_response(jsonify({
            "success": False,
            "message": "User is not owner"}, 401
    ))
 
    return response


@app.route("/login", methods=['POST'])
def authorize_user_credentials():
    mock_username = "admin"  # Replace with actual DB check
    mock_password = "111"    # Replace with password hash check

    request_username = request.json.get('username')
    request_password = request.json.get('password')
    remember = request.json.get('remember')

    if not request_username or not request_password:
        abort(400, description="Username and password are required")

    if request_username != mock_username or request_password != mock_password:
        abort(401, description="User not found")

    
    response = make_response(jsonify({
        "success": True,
        "message": "Authorization successful"}, 200
    ))
    
    if remember:
        token = generate_jwt({"user_id": request_username, "exp":datetime.now(UTC) + timedelta(days=14)})
        
        generate_cookie(response, token, True)
        
    else:
        token = generate_jwt({"user_id": request_username})
        
        generate_cookie(response, token, False)
        
    return response


@app.route("/register", methods=['POST'])
def register_user():
    request_username = request.json.get('username')
    request_password = request.json.get('password')
    # Server-side validation
    if not request_username or not request_password:
        abort(400, description="Username and password are required")

    if not re.match(r'^[a-zA-Z0-9\s]*$', request_username):
        abort(400, description="Username Invalid")

    if len(request_password) < 8:
        abort(400, description="Password must be at least 8 characters long")

    hashed_password = bcrypt.hashpw(request_password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        register_user_db(request_username, hashed_password)
    except Exception as e:
        abort(500, description=f"Database request failed with following error: {e}")
    else:
        response = make_response(jsonify({
            "success": True,
            "message": "Registration successful"}, 200
        ))

        token = generate_jwt({"user_id": 1, "exp":datetime.now(UTC) + timedelta(days=14)})
        
        generate_cookie(response, token, True)
            
        return response

@app.route("/auth", methods=['GET'])
@token_required
def authorize_user_cookie(user_id):
    '''Fetches user_id (login so far) from browser-saved cookie and returns it to the frontend.
    If no cookie is supplied (only happens when cookie is absent/outdated) then bad request is returned.'''
    
    if not user_id:
        response = make_response(jsonify({
        "success": False,
        "message": "Credentials not found",}, 401
    ))
    
    response = make_response(jsonify({
        "success": True,
        "message": "Authorization successful",
        "user_id": user_id}, 200
    ))
    
    return response

@app.route("/can_rate_tutor", methods=['POST'])
@token_required
def can_rate_tutor(current_user):
    tutor_id = request.json.get('tutor_id')
    user_id = current_user

    if not tutor_id:
        abort(400, description="Tutor ID is required")

    try:
        from database import can_get_rated
        can_be_rated = can_get_rated(tutor_id, user_id)

        if can_be_rated:
            response = make_response(jsonify({
                "success": True,
                "message": "Tutor can be rated"
            }), 200)
        else:
            response = make_response(jsonify({
                "success": False,
                "message": "Tutor cannot be rated"
            }), 400)

    except Exception as e:
        abort(500, description=f"Error checking tutor rating: {e}")

    return response 

if __name__ == "__main__":
    app.run(debug=True)