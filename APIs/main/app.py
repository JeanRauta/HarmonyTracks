from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS
import random
import hashlib
import requests

app = Flask(__name__)

CORS(app)

client = MongoClient('mongodb+srv://jean:gincana@teste.0nxua.mongodb.net/')
db = client['teste_db']
sessions_collection = db['sessions']  

sessions_collection.create_index("createdAt", expireAfterSeconds=10)

def obter_token():
    token = hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()
    
    existing_token = sessions_collection.find_one({"token_sessao": token})

    if existing_token is None:
        sessions_collection.insert_one({"token_sessao": token, "createdAt": datetime.utcnow()})
    else:
        token = existing_token['token_sessao']

    return token

def salvar_dados(token, tipo, dados):
    session_data = sessions_collection.find_one({"token_sessao": token})

    if session_data:
        sessions_collection.update_one(
            {"token_sessao": token},
            {"$set": {f"dados.{tipo}": dados}}  
        )
    else:
        new_session = {
            "token_sessao": token,
            "dados": {
                tipo: dados  
            },
            "createdAt": datetime.utcnow() 
        }
        sessions_collection.insert_one(new_session)

@app.route('/api/iniciar-sessao', methods=['POST'])
def iniciar_sessao():
    token = request.headers.get('Authorization')
    
    if token and sessions_collection.find_one({"token_sessao": token.split(" ")[1]}):
        return jsonify({"token_sessao": token.split(" ")[1]}) 

    token = obter_token()  
    return jsonify({"token_sessao": token})

@app.route('/api/renovar-token', methods=['POST'])
def renovar_token():
    token = request.headers.get('Authorization').split(" ")[1]
    
    session_data = sessions_collection.find_one({"token_sessao": token})
    
    if not session_data:
        return jsonify({"error": "Token inválido ou expirado."}), 401

    sessions_collection.update_one(
        {"token_sessao": token},
        {"$set": {"createdAt": datetime.utcnow()}}
    )
    
    return jsonify({"message": "Token renovado com sucesso."})


@app.route('/api/separar-faixas', methods=['POST'])
def separar_faixas():
    token = request.headers.get('Authorization').split(" ")[1]
    
    if sessions_collection.find_one({"token_sessao": token}):
        audio_file = request.files.get('file')
        model = request.form.get('model')

        try:
            response = requests.post('http://localhost:5001/separar-faixas', files={'file': audio_file}, data={'model': model})
            resultado = response.json()

            original_filename = resultado.get("original_filename")
            faixas_separadas = {
                "original_filename": original_filename,
                "audio_tags": resultado.get("audio_tags", [])
            }

            salvar_dados(token, "faixas_separadas", faixas_separadas)
            return jsonify(faixas_separadas)
        except Exception as e:
            return jsonify({"error": f"Ocorreu um erro: {str(e)}"}), 500
    else:
        return jsonify({"error": "Token inválido ou expirado."}), 401

@app.route('/api/identificar-acordes', methods=['POST'])
def identificar_acordes():
    token = request.headers.get('Authorization').split(" ")[1]
    
    if sessions_collection.find_one({"token_sessao": token}):
        data = request.get_json()
        urls = data.get('urls', [])

        if not urls:
            return jsonify({'error': 'Nenhuma URL fornecida'}), 400
        
        try:
            response = requests.post('http://localhost:5002/identificar-acordes', json={'urls': urls})
            acordes_resultado = response.json()

            salvar_dados(token, "acordes_identificados", acordes_resultado)

            return jsonify(acordes_resultado)
        except Exception as e:
            return jsonify({"error": f"Ocorreu um erro: {str(e)}"}), 500
    else:
        return jsonify({"error": "Token inválido ou expirado."}), 401


@app.route('/api/converter-midi', methods=['POST'])
def converter_midi():
    token = request.headers.get('Authorization').split(" ")[1]

    if sessions_collection.find_one({"token_sessao": token}):
        data = request.get_json()
        audio_url = data.get('audio_url')

        if not audio_url:
            return jsonify({'error': 'Nenhuma URL de áudio fornecida'}), 400

        try:
            response = requests.post('http://localhost:5003/convert_to_midi', json={'audio_url': audio_url})
            resultado = response.json()

            salvar_dados(token, "midi_converted", resultado)
            return jsonify(resultado)
        except Exception as e:
            return jsonify({"error": f"Ocorreu um erro: {str(e)}"}), 500
    else:
        return jsonify({"error": "Token inválido ou expirado."}), 401

