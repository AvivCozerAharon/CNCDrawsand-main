import time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import serial

arduino = serial.Serial(port='COM28', baudrate=115200, timeout=.1) 
client = MongoClient("localhost", 27017)
database = client["CNCDrawing"]
collection = database["drawings"]

# Inicialização do Flask
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

    if not data:
        return jsonify({"error": "No data provided"}), 400

    drawing_data = {
        "drawing": data.get("drawingData"),
        "name": data.get("draw_name"),
        "location": data.get("draw_location"),
        "created_at": datetime.now(),  
        "status": "queued"  
    }

    result = collection.insert_one(drawing_data)
    return jsonify({"message": "Desenho enviado com sucesso!", "id": str(result.inserted_id)}), 201

@app.route("/send_to_cnc", methods=["GET"])
def send_to_cnc():
    next_drawing = collection.find_one_and_update(
        {"status": "queued"},
        {"$set": {"status": "processing"}},  
        sort=[("created_at", 1)],  
        return_document=True  
    )    

    if not next_drawing:
        return jsonify({"message": "Nenhum desenho na fila para enviar."}), 404
    try:
        print(f"Enviando desenho ao CNC: {next_drawing['_id']}")
        collection.update_one(
            {"_id": next_drawing["_id"]},
            {"$set": {"status": "done"}}
        )
        string_to_send = ""
        for position in next_drawing["drawing"]:
            if position['x'] is not None and position['y'] is not None:
                string_to_send += f"{position['x']:.1f},{position['y']:.1f} "
        string_to_send += "\n"
        print(string_to_send)
        arduino.write(string_to_send.encode())
        arduino.write(b'positions')
        return jsonify({"message": "Desenho enviado com sucesso!", "id": str(next_drawing["_id"]), "name": str(next_drawing['name']),"location": str(next_drawing['location'])}), 200
    except Exception as e:
        collection.update_one(
            {"_id": next_drawing["_id"]},
            {"$set": {"status": "queued"}}
        )
        return jsonify({"error": f"Falha ao enviar desenho: {e}"}), 500

@app.route('/camera/<drawing_id>')
def camera_page(drawing_id):
    try:
        current_drawing = collection.find_one({"_id": ObjectId(drawing_id)})

        if not current_drawing:
            return jsonify({"error": "Desenho não encontrado"}), 404

        position = collection.count_documents({
            "status": "queued",
            "created_at": {"$lt": current_drawing["created_at"]}
        })

        return render_template('camera.html', position=position)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/queue_position/<drawing_id>', methods=["GET"])
def queue_position(drawing_id):
    try:
        current_drawing = collection.find_one({"_id": ObjectId(drawing_id)})

        if not current_drawing:
            return jsonify({"error": "Desenho não encontrado"}), 404

        position = collection.count_documents({
            "status": "queued",
            "created_at": {"$lt": current_drawing["created_at"]}
        })

        return jsonify({"position": position}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(port=5000, debug=False)
