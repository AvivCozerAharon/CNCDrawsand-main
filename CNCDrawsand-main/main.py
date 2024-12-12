import time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from serial import *
import threading
import requests

arduino = Serial(port='COM13', baudrate=115200, timeout=.1) 
client = MongoClient("localhost", 27017)
database = client["CNCDrawing"]
collection = database["drawings"]

time.sleep(2)
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

def send_to_adulterado():
    try:
        string = "605.7,284.7,SINGLE 605.1,289.1,SINGLE 604.6,293.6,SINGLE 604.0,298.0,SINGLE 604.0,298.0,SINGLE 602.0,301.7,SINGLE 600.0,305.3,SINGLE 598.0,309.0,SINGLE 596.0,312.7,SINGLE"
        arduino.write(string.encode('utf-8'))
        return 1
    except:
        return 0

def send_to_cnc():
    next_drawing = collection.find_one_and_update(
        {"status": "queued"},
        {"$set": {"status": "processing"}},  
        sort=[("created_at", 1)],  
        return_document=True  
    )    

    if not next_drawing:
        return -1
    try:
        print(f"Enviando desenho ao CNC: {next_drawing['_id']}")
        collection.update_one(
            {"_id": next_drawing["_id"]},
            {"$set": {"status": "done"}}
        )

        string_to_send = ""
        for index, position in enumerate(next_drawing["drawing"]):
            if position['x'] is not None and position['y'] is not None and index != 0:
                #last_position = next_drawing["drawing"][index - 1]
                #if last_position['x'] or last_position['y'] is None:
                #    continue
                #diff_x = abs(position['x'] - last_position['x'])
                #diff_y = abs(position['y'] - last_position['y'])
                #diff_relative = 1
                #if diff_x < diff_relative and diff_y < diff_relative:
                #    continue

                if position['size'] == 1:
                    shovel_size = 'SINGLE'
                elif position['size'] == 3:
                    shovel_size = 'THREE'
                else:
                    shovel_size = 'OFF'
                string_to_send += f"{2.5*position['x']:.0f},{2.5*position['y']:.0f},{shovel_size} "
                print("etapa ", index + 1)

        string_to_send += "\n"
        print(string_to_send)
        print("\n\n")

        lst = string_to_send.split(" ")
        grupos = len(lst)//100
        resto = len(lst)%100
       
        if len(lst) < 100:
                arduino.flush()
                arduino.flushInput()
                arduino.flushOutput()
                
                arduino.write("clear".encode())
                time.sleep(0.05)
                arduino.write(string_to_send.encode('utf-8'))
                print("etapa 2")
                time.sleep(0.1)
                arduino.write(b'positions')
                print("etapa 3")
                time.sleep(0.05)
                return 1
        
        i = 0
        fim = 0
        inicio = 0
        while i < grupos:
            if i == 0:
                string_to_send = " ".join(lst[0:100])
                print("STRING I==0: " + string_to_send)
                arduino.flush()
                arduino.flushInput()
                arduino.flushOutput()
                
                arduino.write("clear".encode())
                time.sleep(0.05)
                arduino.write(string_to_send.encode('utf-8'))
                print("etapa 2")
                time.sleep(0.1)
                arduino.write(b'positions')
                print("etapa 3")
                time.sleep(0.05)
                i += 1
            else:
                data = arduino.readline().decode('utf-8').strip()
                print(data)
                if data == "0":
                    if i == grupos:
                        inicio = grupos * 100
                        fim = inicio + resto
                        string_to_send = " ".join(lst[inicio:fim])
                        print("STRING I == GRUPOS: " + string_to_send)
                        arduino.flush()
                        arduino.flushInput()
                        arduino.flushOutput()

                        arduino.write("clear".encode())
                        time.sleep(0.05)
                        arduino.write(string_to_send.encode('utf-8'))
                        print("etapa 2")
                        time.sleep(0.05)
                        arduino.write(b'positions')
                        print("etapa 3")
                        time.sleep(0.05)
                    else:
                        fim = (i+1)*100
                        inicio = i*100
                        string_to_send = " ".join(lst[inicio:fim])
                        print("STRING I: " + string_to_send)
                        arduino.flush()
                        arduino.flushInput()
                        arduino.flushOutput()

                        arduino.write("clear".encode())
                        time.sleep(0.05)
                        arduino.write(string_to_send.encode('utf-8'))
                        print("etapa 2")
                        time.sleep(0.05)
                        arduino.write(b'positions')
                        print("etapa 3")
                        time.sleep(0.05)
                    i += 1

        return 1
    except Exception as e:
        print(e)
        collection.update_one(
            {"_id": next_drawing["_id"]},
            {"$set": {"status": "queued"}}
        )
        return 0

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
            if arduino.in_waiting:
                data = arduino.readline().decode('utf-8').strip()
                print(data)
                if data == '0':
                    print("Arduino está pedindo um desenho!")
                    response = send_to_cnc()
                    if response == 1:
                        print("Desenho enviado para o CNC com sucesso!")
                    elif response == 0:
                        print("Falha ao enviar desenho para o CNC.")  
                    else:
                        print("Fila vazia.")     
        except Exception as e:
            print(f"Erro ao ler do Arduino: {e}")
        
if __name__ == '__main__':
    arduino_thread = threading.Thread(target=read_from_arduino)
    arduino_thread.daemon = True 
    arduino_thread.start()

    app.run(port=5000, debug=False)
