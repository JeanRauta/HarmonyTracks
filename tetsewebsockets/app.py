from pymongo import MongoClient
from flask_socketio import SocketIO, emit
from flask import Flask, request
from datetime import datetime
from flask_cors import CORS
import threading

# Configuração do Flask e Socket.IO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuração do MongoDB
client = MongoClient('mongodb+srv://jean:gincana@teste.0nxua.mongodb.net/')
db = client['teste']
collection = db['temporary_users']

# Dicionário para armazenar timers de desconexão
disconnection_timers = {}

# Função para excluir o usuário do MongoDB
def remove_user(user_id):
    print(f"Removendo usuário inativo: {user_id}")
    collection.delete_one({'user_id': user_id})
    disconnection_timers.pop(user_id, None)  # Remove o timer do dicionário

# Evento de conexão WebSocket
@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id:
        print(f"Usuário {user_id} conectado.")
        
        # Cancelar o timer se já existir (o usuário reconectou antes do tempo expirar)
        if user_id in disconnection_timers:
            disconnection_timers[user_id].cancel()
            del disconnection_timers[user_id]  # Remover o timer do dicionário
            
        # Armazenar informações no MongoDB ou atualizar se já existir
        collection.update_one(
            {'user_id': user_id},
            {'$set': {'last_active': datetime.now(), 'status': 'online'}},
            upsert=True
        )
        emit('connected', {'message': 'Conexão estabelecida com sucesso'})

# Evento de desconexão WebSocket
@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.args.get('user_id')
    if user_id:
        print(f"Usuário {user_id} desconectado.")
        
        # Inicia um timer de 10 segundos para remover o usuário
        timer = threading.Timer(10.0, remove_user, args=(user_id,))
        timer.start()
        
        # Armazenar o timer no dicionário
        disconnection_timers[user_id] = timer

# Evento para processar "ping" de atividade do usuário
@socketio.on('user_ping')
def handle_ping(data):
    user_id = data.get('user_id')
    print(f"Ping recebido de {user_id}")
    # Atualiza o timestamp de última atividade no MongoDB
    collection.update_one(
        {'user_id': user_id},
        {'$set': {'last_active': datetime.now(), 'status': 'online'}}
    )
    emit('pong', {'message': 'Ping recebido'})

# Função para verificar usuários inativos
def verificar_inatividade():
    while True:
        # Verifica usuários a cada 5 segundos (opcional, não necessariamente para remoção)
        socketio.sleep(5)

# Inicia a verificação de inatividade em segundo plano
def iniciar_verificacao():
    socketio.start_background_task(verificar_inatividade)

if __name__ == '__main__':
    iniciar_verificacao()
    socketio.run(app, debug=True)
