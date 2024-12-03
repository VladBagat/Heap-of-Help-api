from flask import Flask, request, jsonify, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins":"https://heap-of-help.vercel.app"}})

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

from flask import Flask, request, jsonify, abort

app = Flask(__name__)

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

    return jsonify({
        "success": True,
        "message": "Authorization successful"
    }), 200



       
