from flask import Flask,request, jsonify    #JSON
from flask_cors import CORS                 #potrzebna biblioteka

app = Flask(__name__)
CORS(app)  
 
print("work app")

public_url ="przykładowy adres"

@app.route("/get-url", methods=["GET"])
def get_url():
    return jsonify({"url": public_url})

@app.route("/message", methods=["GET"])     #wysyłanie wiadmości
def get_message():
    return jsonify({"message": "Witaj w API! "})
    

@app.route("/send_data",methods=["POST"])   #pobieranie danych
def recive_data():
    
    data=request.get_json()
    if not data:
        return jsonify({"error": "No data "}), 400
    print("dane: ",data)
    return jsonify({"message": "received", "data": data}), 200
    
        
if __name__ == "__main__":          #uruchomienie serwera
    app.run(host='0.0.0.0',port=5000)
