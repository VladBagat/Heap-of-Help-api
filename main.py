from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
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

@app.route("/hello")
@token_required
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/login", methods=['POST'])
def authorize_user():
    mock_username = "admin"  # Replace with actual DB check
    mock_password = "111"    # Replace with password hash check

    request_username = request.json.get('username')
    request_password = request.json.get('password')

    if not request_username or not request_password:
        abort(400, description="Username and password are required")

    if request_username != mock_username:
        abort(401, description="User not found")

    if request_password != mock_password:
        abort(401, description="Invalid credentials")
        
    token = generate_jwt({"user_id": 1, "exp":datetime.utcnow() + timedelta(days=7)})
    
    response = make_response(jsonify({
        "success": True,
        "message": "Authorization successful"}, 200
    ))

    response.set_cookie(
        "jwt", 
        token, 
        httponly=True, 
        secure=True, 
        samesite="Strict"
    )
    
    return response

