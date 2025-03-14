from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from os import getenv
import json

from database import fetch_tutor_tags, fetch_recommended_tutors, fetch_user_tags, users_table_setup, tags_table_setup, login_user_db, get_tutee_profile, tutees_table_setup, is_tutor, get_tutor_profile, tutors_table_setup, register_tutor, register_tutee, validate_username
from utils import token_required, tag_encoder
import re
import bcrypt
import base64
import requests

from utils import token_required
from ranking import RankingAlgorithm
from Ranking.lookup_table import LookupTableGenerator


app = Flask(__name__)

#TODO : This area will be substitues with __init__ when we will move this to a class. 
ra = RankingAlgorithm()
LookupTableGenerator().generate_lookup_table()
#DATABASE SETUP
users_table_setup()
tags_table_setup()  

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
    expired_token = generate_jwt({"user_id": "invalid", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)})
    
    response = make_response(jsonify({
        "success": True,
        "message": "Logged out successfully"
    }))
    
    # Set the JWT cookie to expire immediately
    response.set_cookie(
        "jwt", 
        expired_token,  # Set an expired JWT
        httponly=True, 
        secure=True, 
        samesite="None",
        expires=0  # Expire immediately
    )
    
    return response

@app.route("/validate_username", methods=['POST'])
def username_validation():
    request_username = request.json.get('username')
    success = validate_username(request_username)
    
    if success:
        response = make_response(jsonify({
            "success": True,
            "message": "No duplicate username"}, 200
        ))
    else:
        response = make_response(jsonify({
            "success": False,
            "message": "Username exists"}, 403
        ))
    return response


@app.route("/registration", methods=['POST'])
def register_user():
    request_profile = request.json.get('profile')
    request_username = request.json.get('username')
    request_password = request.json.get('password')
    request_forename = request.json.get('forename')
    request_surname = request.json.get('surname')
    request_age = request.json.get('age')
    request_email = request.json.get('email')
    request_language = request.json.get('language')
    request_timezone = request.json.get('timezone')
    request_description = request.json.get('description')
    request_education = request.json.get('education')
    request_profile_img = request.json.get('profile_img')
    request_tags = request.json.get("selectedTags")
    
    # Server-side validation
    if not request_username or not request_password:
        abort(400, description="Username and password are required")

    if not re.match(r'^[a-zA-Z0-9_\-@\.!#$%&*+=()\[\]{}|:,?~£¥]*$',request_username):
        abort(400, description="Username Invalid")

    if len(request_password) < 8:
        abort(400, description="Password must be at least 8 characters long")

    hashed_password = bcrypt.hashpw(request_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
    tag_list = []
    for t in request_tags:
        tag_list.append(tag_encoder(t))
        
    try:
        if request_profile == "tutor":
            success = register_tutor(
                            request_username,
                            hashed_password,
                            request_forename,
                            request_surname,
                            request_email,
                            request_age,
                            request_language,
                            request_timezone,
                            request_description,
                            request_education,
                            request_profile_img,
                            tag_list
                        )
        elif request_profile == 'tutee':
            success = register_tutee(
                            request_username,
                            hashed_password,
                            request_forename,
                            request_surname,
                            request_email,
                            request_age,
                            request_language,
                            request_timezone,
                            request_description,
                            request_education,
                            request_profile_img,
                            tag_list
                        )
    except Exception as e:
        abort(500, description=f"Database request failed with following error: {e}")
    
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


@app.route('/get_tutor_profile', methods=['POST'])
def get_tutor():
    tutor_id = request.json.get('id')
    print(tutor_id)
    tutor_profile = get_tutor_profile(tutor_id)

    if tutor_profile:
        response = make_response(jsonify({
            "success": True,
            "message": "Tutor profile found",
            "data": tutor_profile
        }), 200)
    else:
        response = make_response(jsonify({
            "success": False,
            "message": "Tutor profile not found"
        }), 401)
    
    return response

@app.route("/content", methods=['GET'])
@token_required
def fetch_content(user_id):
    user_tags = list(fetch_user_tags(user_id))[0]  
    user_tags = [tag for tag in user_tags if tag is not None]
    item_tags_list = fetch_tutor_tags()
    
    item_tags_dict = {}
    
    result_dict = {}
    
    for item in item_tags_list:
        item_tags_dict.update({item[1]: list(item[2:])})
                
    for key, value in item_tags_dict.items():
        value = [tag for tag in value if tag is not None]
        result_dict.update({key: ra.calculate_content_score(user_tags, value)})
            
    results = [key for key, _ in sorted(result_dict.items(), key=lambda x: x[1]['final_score'], reverse=True)[:10]]
        
    # Maybe use Andy's tutor fetch
    items = fetch_recommended_tutors(results)
    
    item_tags_dict = {key: [x for x in value if x is not None] for key, value in item_tags_dict.items()}
    
    items = [{"user_id": results[index], "first_name": item[0], "last_name": item[1], "description": item[2],
            "profile_img": base64.b64encode(item[3]).decode('utf-8'),
            "tags":LookupTableGenerator.convert_int_to_tag(item_tags_dict[results[index]])} for index, item in enumerate(items)]
    
    response = make_response(jsonify({
        "success": True,
        "message": f"Fetched {len(items)} items",
        "content": items}, 200)
    )
            
    return response


@app.route("/news", methods=['GET'])
def fetch_news():
    """Fetches news content for user"""
    key = getenv("NEWS_KEY")
    params = {
        'category': 'technology',
        'language': 'en',  # Doesn't seem to get other languages
        'sortBy': 'popularity',
        'pageSize': 7,
        'apiKey': key
    }
    try:
        response = requests.get("https://newsapi.org/v2/top-headlines",
                                params=params).json()['articles']
        return response
    except:
        return "Failed to fetch news"


@app.route("/more_news", methods=['GET'])
def fetch_more_news():
    # Allows user to fetch more news up to 5 times
    page = request.args.get("page")
    search = request.args.get("search")
    key = getenv("NEWS_KEY")
    params = {
        'category': 'technology',
        'language': 'en',
        'q': search,
        'sortBy': 'publishedAt',
        'pageSize': 7,
        'page': page,
        'apiKey': key
    }
    try:
        response = requests.get("https://newsapi.org/v2/top-headlines",
                                params=params).json()['articles']

        return response
    except:
        return "Failed to fetch news"


@app.route("/search_news", methods=['GET'])
def fetch_search_news():
    search = request.args.get("search")
    page = request.args.get("page")
    key = getenv("NEWS_KEY")
    params = {
        'category': 'technology',
        'q': search,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 7,
        'page': page,
        'apiKey': key
    }
    try:
        response = requests.get("https://newsapi.org/v2/top-headlines",
                                params=params).json()['articles']
        return response
    except:
        return "Failed to fetch news"


if __name__ == "__main__":
    tutees_table_setup()
    app.run(port=8000, debug=True)
