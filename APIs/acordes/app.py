from flask import Flask, request, jsonify, send_file
import requests
from chord_extractor.extractors import Chordino
import tempfile
import os
from pydub import AudioSegment
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

@app.route('/identificar-acordes', methods=['POST'])
def identificar_acordes():
    try:
        data = request.get_json()  
        urls = data.get('urls', [])  

        if not urls:
            return jsonify({'error': 'Nenhuma URL fornecida'}), 400
        
        print(f"Recebendo URLs: {urls}") 

        temp_file_paths = []
        audio_segments = []

        for url in urls:
            print(f"Baixando áudio de: {url}")  
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file_paths.append(temp_file_path)
                download_audio(url, temp_file_path)
                audio_segment = AudioSegment.from_wav(temp_file_path)
                audio_segments.append(audio_segment)

        if not audio_segments:
            raise Exception("Nenhum áudio foi baixado.")

        max_length = max(len(seg) for seg in audio_segments)
        audio_segments = [seg + AudioSegment.silent(duration=max_length - len(seg)) for seg in audio_segments]

        combined = audio_segments[0]
        for seg in audio_segments[1:]:
            combined = combined.overlay(seg)
        
        combined_file_path = tempfile.mktemp(suffix='.wav')
        combined.export(combined_file_path, format='wav')
        
        chordino = Chordino()
        acordes = chordino.extract(combined_file_path)
        acordesC = [{'chord': acorde.chord, 'timestamp': acorde.timestamp} for acorde in acordes]

        json_file_path = tempfile.mktemp(suffix='.json')
        with open(json_file_path, 'w') as json_file:
            json.dump({'acordes': acordesC}, json_file)

        for path in temp_file_paths:
            os.remove(path)
        os.remove(combined_file_path)

        return send_file(json_file_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_audio(audio_url, temp_file_path):
    try:
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

        audio_segment = AudioSegment.from_file(temp_file_path, format='mp3')
        audio_segment.export(temp_file_path, format='wav')
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao baixar o áudio: {e}")
    except Exception as e:
        raise Exception(f"Erro ao processar o áudio: {e}")
    
