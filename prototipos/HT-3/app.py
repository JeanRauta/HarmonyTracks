import os
import uuid
import demucs.separate
from flask import Flask, render_template, request
import demucs.api
import yt_dlp as youtube_dl
import torchaudio
from chord_extractor.extractors import Chordino

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/separar', methods=['POST'])
def separar():
    try:
        if not os.path.exists("./static/audio_base"):
            os.makedirs("./static/audio_base")

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            filename = file.filename.replace(" ", "_")
            audio_path = os.path.join("./static/audio_base", filename)
            file.save(audio_path)
        elif 'url' in request.form and request.form['url'] != '':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': './static/audio_base/teste.%(ext)s',
            }
            youtube_url = request.form['url']
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            audio_path = "./static/audio_base/teste.wav"
        else:
            return "Nenhum arquivo ou URL fornecido"
        
        unique_folder_name = str(uuid.uuid4())
        output_folder = f"./static/{unique_folder_name}"
        os.makedirs(output_folder)

        selected_model = request.form.get('model')

        if selected_model == "d6":
            separator = demucs.api.Separator(model="htdemucs_6s", progress=True, device='cuda', jobs=2)
        elif selected_model == "d4":
            separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cuda', jobs=2)
        elif selected_model == "d2":
            separator = demucs.api.Separator(model="htdemucs_ft", progress=True, device='cuda', jobs=2)
        else:
            return "Modelo não suportado."

        origin, separated = separator.separate_audio_file(audio_path)

        chordino = Chordino()
        acordes = chordino.extract(audio_path)
        acordesC = [{'chord': acorde.chord, 'timestamp': acorde.timestamp} for acorde in acordes]

        audio_tags = []

        if selected_model == "d2":
            instrumental = separated['bass'] + separated['other'] + separated['drums']
            instrumental_path = f"{output_folder}/instrumental.wav"
            torchaudio.save(instrumental_path, instrumental, sample_rate=44100)
            audio_tags.append({'src': f"/static/{unique_folder_name}/instrumental.wav", 'name': 'instrumental'})

            vocals_path = f"{output_folder}/vocals.wav"
            torchaudio.save(vocals_path, separated['vocals'], sample_rate=44100)
            audio_tags.append({'src': f"/static/{unique_folder_name}/vocals.wav", 'name': 'vocals'})
        else:
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
