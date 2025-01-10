from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from os import getenv
from utils import token_required

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
        httponly=False, #True
        secure=True, #True
        samesite="None",
        domain=request.headers.get('Origin'),
        expires=expires
        )
    
    return response

@app.route("/hello", methods=['GET'])
@token_required
def hello_world(current_user):
    return "<p>Hello, World!</p>"

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

@app.route("/auth", methods=['GET'])
@token_required
def authorize_user_cookie(user_id):
    
    print(user_id)
    
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

if __name__ == "__main__":
    app.run(debug=True)