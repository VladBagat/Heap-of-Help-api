from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows unrestricted internet access. CRITICAL!!!

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/hello", methods=['GET'])
def hello_world1():
    return "I am a sigma sigma John Pork!"