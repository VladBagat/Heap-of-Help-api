from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/hello", methods=['GET'])
def hello_world1():
    return "I am a sigma sigma John Pork!"