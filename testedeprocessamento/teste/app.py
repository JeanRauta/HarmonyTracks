import os
import uuid
import tempfile
import demucs.separate
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import demucs.api
import yt_dlp as youtube_dl
import torchaudio
from pymongo import MongoClient
import gridfs
import threading

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://jean:gincana@teste.0nxua.mongodb.net/")
db = client['audio_database'] 
fs = gridfs.GridFS(db) 

gpu_semaphore = threading.Semaphore(1)

@app.route('/separar', methods=['POST'])
def separar():
    try:
        with gpu_semaphore:
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = None
                original_filename = None
                
                if 'file' in request.files and request.files['file'].filename != '':
                    file = request.files['file']
                    original_filename = os.path.splitext(file.filename.replace(" ", "_"))[0]
                    audio_path = os.path.join(temp_dir, "origin.wav")
                    file.save(audio_path)
                elif 'url' in request.form and request.form['url'] != '':
                    youtube_url = request.form['url']
                    
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'wav',
                            'preferredquality': '192',
                        }],
                        'outtmpl': os.path.join(temp_dir, 'origin.%(ext)s'),
                    }
                    
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        info_dict = ydl.extract_info(youtube_url, download=True)
                        original_filename = os.path.splitext(info_dict['title'])[0]
                        audio_path = os.path.join(temp_dir, "origin.wav")
                else:
                    return jsonify({"error": "Nenhum arquivo ou URL fornecido"}), 400
                
                unique_folder_name = str(uuid.uuid4())
                output_folder = os.path.join(temp_dir, unique_folder_name)
                os.makedirs(output_folder)

                selected_model = request.form.get('model')
                if selected_model == "d6":
                    separator = demucs.api.Separator(model="htdemucs_6s", progress=True, device='cuda', jobs=2)
                elif selected_model == "d4":
                    separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cuda', jobs=2)
                elif selected_model == "d2":
                    separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cuda', jobs=2)
                else:
                    return jsonify({"error": "Modelo não suportado."}), 400

                origin, separated = separator.separate_audio_file(audio_path)

                audio_tags = []

                for source_name, source_data in separated.items():
                    sanitized_source_name = source_name.replace(" ", "_")
                    output_path = os.path.join(output_folder, f"{sanitized_source_name}.wav")
                    torchaudio.save(output_path, source_data, sample_rate=44100)

                    with open(output_path, "rb") as audio_file:
                        file_id = fs.put(audio_file, filename=f"{original_filename}_{sanitized_source_name}.wav")
                        audio_tags.append({'file_id': str(file_id), 'name': sanitized_source_name})

                response_data = {
                    "original_filename": original_filename,
                    "audio_tags": audio_tags
                }

                return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro: {e}"}), 500

from bson import ObjectId

@app.route('/download', methods=['GET'])
def download_file():
    try:
        file_id = request.args.get('file_id')
        if not file_id:
            return jsonify({"error": "file_id é necessário"}), 400
        
        try:
            file_id = ObjectId(file_id)
        except Exception as e:
            return jsonify({"error": f"ID de arquivo inválido: {e}"}), 400
        
        file = fs.get(file_id)
        return send_file(file, download_name=file.filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Arquivo não encontrado: {e}"}), 404

if __name__ == "__main__":
    app.run(threaded=True)
