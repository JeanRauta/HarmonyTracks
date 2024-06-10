import os
import uuid
import json
from flask import Flask, render_template, request
import demucs.api
import torchaudio
from pytube import YouTube
from chord_extractor.extractors import Chordino

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/separar', methods=['POST'])
def separar():
    try:
        if not os.path.exists("./static/audio_test"):
            os.makedirs("./static/audio_test")

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            filename = file.filename.replace(" ", "_")
            audio_path = os.path.join("./static/audio_test", filename)
            file.save(audio_path)
        elif 'url' in request.form and request.form['url'] != '':
            youtube_url = request.form['url']
            yt = YouTube(youtube_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            download_path = audio_stream.download(output_path="./static/audio_test")
            base, ext = os.path.splitext(download_path)
            sanitized_base = base.replace(" ", "_")
            audio_path = sanitized_base + ".mp3"
            os.rename(download_path, audio_path)
        else:
            return "Nenhum arquivo ou URL fornecido"

        separator = demucs.api.Separator(model="htdemucs_6s")

        origin, separated = separator.separate_audio_file(audio_path)

        chordino = Chordino()
        acordes = chordino.extract(audio_path)
        acordesC = [{'chord': acorde.chord, 'timestamp': acorde.timestamp} for acorde in acordes]

        unique_folder_name = str(uuid.uuid4())
        output_folder = f"./static/{unique_folder_name}"
        os.makedirs(output_folder)
        
        audio_tags = []
        for source_name, source_data in separated.items():
            sanitized_source_name = source_name.replace(" ", "_")
            output_path = f"{output_folder}/{sanitized_source_name}.wav"
            torchaudio.save(output_path, source_data, sample_rate=44100)
            audio_tags.append({'src': f"/static/{unique_folder_name}/{sanitized_source_name}.wav", 'name': sanitized_source_name})

        return render_template('audios.html', audio_tags=audio_tags, acordes=acordesC)
    
    except Exception as e:
        return f"Ocorreu um erro: {e}"

if __name__ == "__main__":
    app.run(debug=True)
