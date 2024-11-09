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
import boto3
import pydub

app = Flask(__name__)
CORS(app)


S3_BUCKET = 'htracks'  

@app.route('/separar-faixas', methods=['POST'])
def separar_faixas():
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
            selected_model = request.form.get('model')

            if selected_model == "d6":
                separator = demucs.api.Separator(model="htdemucs_6s", progress=True, device='cuda', jobs=2)
            elif selected_model == "d4":
                separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cuda', jobs=2)
            elif selected_model == "d2":
                separator = demucs.api.Separator(model="htdemucs", progress=True, device='cuda', jobs=2)
            else:
                return jsonify({"error": "Modelo não suportado."}), 400

            origin, separated = separator.separate_audio_file(audio_path)

            audio_tags = []

            for source_name, source_data in separated.items():
                sanitized_source_name = source_name.replace(" ", "_")
                output_wav_path = os.path.join(temp_dir, f"{sanitized_source_name}.wav")
                torchaudio.save(output_wav_path, source_data, sample_rate=44100)

                output_mp3_path = os.path.join(temp_dir, f"{sanitized_source_name}.mp3")
                sound = pydub.AudioSegment.from_wav(output_wav_path)
                sound.export(output_mp3_path, format="mp3")

                s3_key = f"{unique_folder_name}/{sanitized_source_name}.mp3"
                s3_client.upload_file(output_mp3_path, S3_BUCKET, s3_key)

                s3_link = f"https://d2vdn8oszh8rp9.cloudfront.net/{s3_key}"
                audio_tags.append({'src': s3_link, 'name': sanitized_source_name})

            response_data = {
                "original_filename": original_filename,
                "audio_tags": audio_tags
            }

            return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro: {e}"}), 500


if __name__ == "__main__":
    app.run(threaded=True, port=5001)