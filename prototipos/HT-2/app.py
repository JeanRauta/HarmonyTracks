import os
import uuid
from flask import Flask, render_template, request
import demucs.api
import yt_dlp as youtube_dl
import torchaudio
from chord_extractor.extractors import Chordino
from pydub import AudioSegment

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
            separator = demucs.api.Separator(model="htdemucs_6s")
        elif selected_model == "d4":
            separator = demucs.api.Separator(model="htdemucs_ft")
        elif selected_model == "spleeter":
            return "Função para spleeter ainda não implementada."

        origin, separated = separator.separate_audio_file(audio_path)

        chordino = Chordino()
        acordes = chordino.extract(audio_path)
        acordesC = [{'chord': acorde.chord, 'timestamp': acorde.timestamp} for acorde in acordes]

        audio_tags = []
        for source_name, source_data in separated.items():
            sanitized_source_name = source_name.replace(" ", "_")
            output_path = f"{output_folder}/{sanitized_source_name}.wav"
            torchaudio.save(output_path, source_data, sample_rate=44100)
            audio_tags.append({'src': f"/static/{unique_folder_name}/{sanitized_source_name}.wav", 'name': sanitized_source_name})

        midi_folder = os.path.join(output_folder, 'midi')
        os.makedirs(midi_folder)

        for source_name, source_data in separated.items():
            if source_name != "drums":
                sanitized_source_name = source_name.replace(" ", "_")
                temp_audio_path = os.path.join(midi_folder, f"{sanitized_source_name}.wav")
                torchaudio.save(temp_audio_path, source_data, sample_rate=44100)
                
                # predict_and_save(
                #     [temp_audio_path],   
                #     midi_folder,        
                #     save_midi=True,     
                #     sonify_midi=False,  
                #     save_model_outputs=False, 
                #     save_notes=False,  
                #     model_or_model_path=ICASSP_2022_MODEL_PATH 
                # )

                os.remove(temp_audio_path) 

        return render_template('audios.html', audio_tags=audio_tags, acordes=acordesC)
    
    except Exception as e:
        return f"Ocorreu um erro: {e}"

if __name__ == "__main__":
    app.run(debug=True)
