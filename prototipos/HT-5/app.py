import os
import uuid
import tempfile
import shutil
import demucs.separate
from flask import Flask, request, jsonify
from flask_cors import CORS
import demucs.api
import yt_dlp as youtube_dl
import torchaudio

app = Flask(__name__)
CORS(app)

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

            original_audio_folder = os.path.join(output_folder, "origin")
            os.makedirs(original_audio_folder)
            original_audio_path = os.path.join(original_audio_folder, "origin.wav")
            shutil.copy(audio_path, original_audio_path)

            if selected_model == "d2":
                instrumental = separated['bass'] + separated['other'] + separated['drums']
                instrumental_path = os.path.join(output_folder, "instrumental.wav")
                torchaudio.save(instrumental_path, instrumental, sample_rate=44100)
                audio_tags.append({'src': f"/static/processed_audios/{unique_folder_name}/instrumental.wav", 'name': 'instrumental'})

                vocals_path = os.path.join(output_folder, "vocals.wav")
                torchaudio.save(vocals_path, separated['vocals'], sample_rate=44100)
                audio_tags.append({'src': f"/static/processed_audios/{unique_folder_name}/vocals.wav", 'name': 'vocals'})
            else:
                for source_name, source_data in separated.items():
                    sanitized_source_name = source_name.replace(" ", "_")
                    output_path = os.path.join(output_folder, f"{sanitized_source_name}.wav")
                    torchaudio.save(output_path, source_data, sample_rate=44100)
                    audio_tags.append({'src': f"/static/processed_audios/{unique_folder_name}/{sanitized_source_name}.wav", 'name': sanitized_source_name})

            static_output_folder = os.path.join("./static/processed_audios", unique_folder_name)
            os.makedirs(static_output_folder)
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    full_file_name = os.path.join(root, file)
                    rel_path = os.path.relpath(full_file_name, output_folder)
                    os.makedirs(os.path.dirname(os.path.join(static_output_folder, rel_path)), exist_ok=True)
                    shutil.move(full_file_name, os.path.join(static_output_folder, rel_path))

            response_data = {
                "original_filename": original_filename,
                "audio_tags": audio_tags
            }

            return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro: {e}"}), 500

if __name__ == "__main__":
    app.run(threaded=True)
