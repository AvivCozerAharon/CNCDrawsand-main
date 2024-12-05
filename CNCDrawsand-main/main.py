import time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import serial
import threading
import requests

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
        for index , position in enumerate(next_drawing["drawing"]):
            if index != 0:
                last_position = next_drawing["drawing"][index - 1]
                diff_x = abs(last_position['x'] - position['x'])
                diff_y = abs(last_position['y'] - position['y'])
                diff_relative = 1
                if diff_x < diff_relative and diff_y < diff_relative:
                    continue
            if position['x'] is not None and position['y'] is not None:
                if position['size'] == 1:
                    shovel_size = 'SINGLE'
                elif position['size'] == 3:
                    shovel_size = 'THREE'
                else:
                    shovel_size = 'OFF'
                string_to_send += f"{position['x']:.1f},{position['y']:.1f},{shovel_size} "
        string_to_send += "\n"
        print(string_to_send)
        print("\n\n\n\n\n")

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
    
def read_from_arduino():
    """
    Função que roda em um thread separado para ler dados do Arduino.
    Ela deve verificar periodicamente o status ou a resposta do Arduino
    sem bloquear o servidor Flask.
    """
    while True:
        try:
            data = arduino.readline().decode('utf-8').strip()
            
            #data = "finished"  
            
            if data == "finished":
                print("Arduino sinalizou que terminou o desenho!")
                response = requests.get('http://127.0.0.1:5000/send_to_cnc')  
                if response.status_code == 200:
                    print("Desenho enviado para o CNC com sucesso!")
                else:
                    print("Falha ao enviar desenho para o CNC.")       
        except Exception as e:
            print(f"Erro ao ler do Arduino: {e}")
        
        time.sleep(1)
if __name__ == '__main__':
    arduino_thread = threading.Thread(target=read_from_arduino)
    arduino_thread.daemon = True 
    arduino_thread.start()

    app.run(port=5000, debug=False)
