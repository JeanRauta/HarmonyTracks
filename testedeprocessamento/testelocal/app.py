import os
import uuid
import tempfile
import logging
import demucs.separate
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import demucs.api
import yt_dlp as youtube_dl
import torchaudio

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

@app.route('/separar', methods=['POST'])
def separar():
    try:
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
            output_folder = os.path.join(UPLOAD_FOLDER, unique_folder_name)
            os.makedirs(output_folder)

            selected_model = request.form.get('model')
            if selected_model == "d6":
                separator = demucs.api.Separator(model="htdemucs_6s", progress=True, device='cpu', jobs=3)
            elif selected_model == "d4":
                separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cpu', jobs=2)
            elif selected_model == "d2":
                separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cpu', jobs=2)
            else:
                return jsonify({"error": "Modelo não suportado."}), 400

            origin, separated = separator.separate_audio_file(audio_path)

            audio_tags = []
            for source_name, source_data in separated.items():
                sanitized_source_name = source_name.replace(" ", "_")
                output_path = os.path.join(output_folder, f"{sanitized_source_name}.wav")
                torchaudio.save(output_path, source_data, sample_rate=44100)

                audio_tags.append({'file_path': output_path, 'name': sanitized_source_name})

            response_data = {
                "original_filename": original_filename,
                "audio_tags": audio_tags
            }

            return jsonify(response_data)

    except Exception as e:
        logging.error(f"Erro no processamento: {e}")
        return jsonify({"error": f"Ocorreu um erro: {e}"}), 500

@app.route('/download', methods=['GET'])
def download_file():
    try:
        file_name = request.args.get('file_name')
        if not file_name:
            return jsonify({"error": "file_name é necessário"}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.exists(file_path):
            return send_file(file_path, download_name=file_name, as_attachment=True)
        else:
            return jsonify({"error": "Arquivo não encontrado"}), 404

    except Exception as e:
        logging.error(f"Erro ao baixar o arquivo: {e}")
        return jsonify({"error": f"Ocorreu um erro: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
