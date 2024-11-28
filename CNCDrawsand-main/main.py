from flask import Flask, render_template,request,jsonify, redirect, url_for
from pymongo import MongoClient, ASCENDING, DESCENDING

client = MongoClient("localhost", 27017)
database = client["CNCDrawing"]
collection = database["drawings"]

app = Flask(__name__)
@app.route("/")
def home():
    return render_template('home.html')
@app.route("/draw")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    print(data)    
    return redirect(url_for('camera_page'))

@app.route('/camera')
def camera_page():
    return render_template('camera.html')

app.run(port=5000, debug=False)