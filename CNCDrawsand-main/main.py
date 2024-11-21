from flask import Flask, render_template,request,jsonify
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
    drawing_data = data.get("drawingData")
    
    if drawing_data:
        collection.insert_one({"drawing": drawing_data})
    
    return jsonify({"message": "Desenho enviado com sucesso!"})

app.run(port=5000, debug=False)