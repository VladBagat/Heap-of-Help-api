from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from os import getenv

from database import register_user_db, login_user_db, get_tutee_profile, tutees_table_setup, is_tutor, get_tutor_profile
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
        expires = datetime.now(timezone.utc) + timedelta(days=14)
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
    request_username = request.json.get('username')
    request_password = request.json.get('password')
    remember = request.json.get('remember')

    if not request_username or not request_password:
        abort(400, description="Username and password are required")

    try:
        status = login_user_db(request_username, request_password)
    except Exception as e:
        print("Error Occurred")
        abort(500, description=f"Database request failed with following error: {e}")
    else:
        if status == 200:
            tutor = is_tutor(request_username)
            response = make_response(jsonify({
                "success": True,
                "message": "Authorisation successful",
                "isTutor": tutor,
                "username": request_username
            }, 200))
            if remember:
                token = generate_jwt({"user_id": request_username,
                                  "exp": datetime.now(timezone.utc) + timedelta(
                                      days=14)})

                generate_cookie(response, token, True)

            else:
                token = generate_jwt({"user_id": request_username})

                generate_cookie(response, token, False)
                
            return response

        elif status == 401:
            response = make_response(jsonify({
                "success": False,
                "message": "Authorization unsuccessful"}, 401
            ))
            return response

        elif status == 404:
            response = make_response(jsonify({
                "success": False,
                "message": "User not found"}, 404
            ))
            return response


@app.route("/logout", methods=['POST'])
def logout():
    response = make_response(jsonify({
        "success": True,
        "message": "Logged out successfully"
    }))
    response.set_cookie("auth_token", "", expires=0)  # Clear the cookie
    return response


@app.route("/register", methods=['POST'])
def register_user():
    request_username = request.json.get('username')
    request_password = request.json.get('password')
    # Server-side validation
    if not request_username or not request_password:
        abort(400, description="Username and password are required")

    if not re.match(r'^[a-zA-Z0-9_\-@\.!#$%&*+=()\[\]{}|:,?~£¥]*$',request_username):
        abort(400, description="Username Invalid")

    if len(request_password) < 8:
        abort(400, description="Password must be at least 8 characters long")

    hashed_password = bcrypt.hashpw(request_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        success = register_user_db(request_username, hashed_password)
    except Exception as e:
        abort(500, description=f"Database request failed with following error: {e}")
    else:
        if success:
            response = make_response(jsonify({
                "success": True,
                "message": "Registration successful"}, 200
            ))
        else:
            response = make_response(jsonify({
                "success": False,
                "message": "Registration unsuccessful, username already exists"}, 403
            ))

        token = generate_jwt({"user_id": request_username, "exp": datetime.now(timezone.utc) + timedelta(days=14)})
        
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
    else:
        response = make_response(jsonify({
            "success": True,
            "message": "Authorization successful",
            "user_id": user_id}, 200
        ))
    
    return response

@app.route('/get_tutee_profile', methods=['GET'])
def get_tutee():
    tutee_profile = get_tutee_profile()

    if tutee_profile:
        response = make_response(jsonify({
            "success": True,
            "message": "Tutee profile found",
            "data": tutee_profile
        }), 200)
    else:
        response = make_response(jsonify({
            "success": False,
            "message": "Tutee profile not found"
        }), 401)
    
    return response


@app.route('/get_tutor_profile', methods=['GET'])
def get_tutor():
    tutor_profile = get_tutor_profile()

    if tutor_profile:
        response = make_response(jsonify({
            "success": True,
            "message": "Tutee profile found",
            "data": tutor_profile
        }), 200)
    else:
        response = make_response(jsonify({
            "success": False,
            "message": "Tutee profile not found"
        }), 401)
    
    return response

if __name__ == "__main__":
    app.run(port=8000, debug=True)
