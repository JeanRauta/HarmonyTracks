from flask import Flask, request, jsonify, send_file
from pydub import AudioSegment
import requests, zipfile, tempfile
from io import BytesIO
import math
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def download_audio(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo: {url}")
    audio = BytesIO(response.content)
    return AudioSegment.from_mp3(audio)

def ajustar_volume(audio, volume_percent):
    if volume_percent == 100:
        return audio  
    ganho_db = 20 * math.log10(volume_percent / 100)
    return audio + ganho_db

def mesclar_audios(audio_list):
    if not audio_list:
        return AudioSegment.silent(duration=1000)  
    base = audio_list[0]
    for audio in audio_list[1:]:
        base = base.overlay(audio)
    return base

@app.route('/upload', methods=['POST'])
def upload_json():
    data = request.get_json()

    if 'Estado das Faixas' not in data or 'extraString' not in data:
        return jsonify({"error": "Dados inválidos ou formato incorreto."}), 400

    faixas = data['Estado das Faixas']
    extra_string = data['extraString']

    try:
        if extra_string == "baixarFaixasSeparadas":
            arquivos = [download_audio(faixa["audioSrc"]) for faixa in faixas]
            buffer_zip = BytesIO()
            with zipfile.ZipFile(buffer_zip, "w") as zip_file:
                for idx, audio in enumerate(arquivos):
                    with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_audio:
                        audio.export(temp_audio.name, format="mp3")
                        zip_file.write(temp_audio.name, f"faixa_{idx+1}.mp3")
            buffer_zip.seek(0)
            return send_file(buffer_zip, mimetype="application/zip", download_name="faixas.zip")
        
        elif extra_string == "baixarPlaybackVocal":
            arquivos = [download_audio(faixa["audioSrc"]) for faixa in faixas if "vocals" not in faixa["audioSrc"]]
            playback = mesclar_audios(arquivos)
            buffer_audio = BytesIO()
            playback.export(buffer_audio, format="mp3")
            buffer_audio.seek(0)
            return send_file(buffer_audio, mimetype="audio/mpeg", download_name="playback_vocal.mp3")

        elif extra_string.startswith("baixarBackintrack"):
            instrumento = extra_string.split("baixarBackintrack")[1].strip().lower()
            arquivos = [download_audio(faixa["audioSrc"]) for faixa in faixas if instrumento not in faixa["audioSrc"]]
            backtrack = mesclar_audios(arquivos)
            buffer_audio = BytesIO()
            backtrack.export(buffer_audio, format="mp3")
            buffer_audio.seek(0)
            return send_file(buffer_audio, mimetype="audio/mpeg", download_name=f"backtrack_{instrumento}.mp3")

        elif extra_string == "baixarMix":
            solos = [faixa for faixa in faixas if faixa["isSolo"]]
            arquivos = []

            if solos:
                for faixa in solos:
                    audio = download_audio(faixa["audioSrc"])
                    audio = ajustar_volume(audio, faixa["volume"])
                    arquivos.append(audio)
            else:
                for faixa in faixas:
                    if faixa["isMute"]:
                        continue
                    audio = download_audio(faixa["audioSrc"])
                    audio = ajustar_volume(audio, faixa["volume"])
                    arquivos.append(audio)

            mix = mesclar_audios(arquivos)
            buffer_audio = BytesIO()
            mix.export(buffer_audio, format="mp3")
            buffer_audio.seek(0)
            return send_file(buffer_audio, mimetype="audio/mpeg", download_name="mix.mp3")

        else:
            return jsonify({"error": "Comando desconhecido."}), 400

    except Exception as e:
        return jsonify({"error": f"Erro ao processar o comando: {str(e)}"}), 500

