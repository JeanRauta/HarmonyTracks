from flask import Flask, request, jsonify
from basic_pitch.inference import predict
import tempfile
import os
import hashlib
import boto3
import requests
import subprocess
from flask_cors import CORS
import shutil

app = Flask(__name__)
CORS(app)



S3_BUCKET = 'htracks'

def extrair_nome_faixa(nome_arquivo):
    faixas_validas = ["guitar", "drums", "bass", "other", "vocals", "piano"]
    nome_base = os.path.basename(nome_arquivo).split('.')[0] 
    if nome_base in faixas_validas:
        return nome_base
    else:
        return "unknown"  

@app.route('/convert_to_midi', methods=['POST'])
def convert_to_midi():
    if 'audio_url' not in request.json:
        return {"error": "No audio URL provided"}, 400
    
    audio_url = request.json['audio_url']

    if not audio_url.startswith("http"):
        return {"error": "Invalid audio URL"}, 400
    
    try:
        response = requests.get(audio_url, stream=True)
        response.raise_for_status() 

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_audio_file.write(chunk)

        model_output, midi_data, note_events = predict(temp_audio_file.name, multiple_pitch_bends=False, melodia_trick=True)
        
        hash_name = hashlib.sha256(audio_url.encode()).hexdigest()
        midi_filename = f"{os.path.basename(audio_url).split('.')[0]}.mid"
        
        nome_faixa = extrair_nome_faixa(audio_url)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as temp_midi_file:
            midi_data.write(temp_midi_file.name)

            abc_filename = temp_midi_file.name.replace('.mid', '.txt')
            subprocess.run(["midi2abc", temp_midi_file.name, "-o", abc_filename], check=True)
            
            s3_key_midi = f"{hash_name}/{midi_filename}"  
            s3_client.upload_file(temp_midi_file.name, S3_BUCKET, s3_key_midi)
            s3_link_midi = f"https://d2vdn8oszh8rp9.cloudfront.net/{s3_key_midi}"
            
            s3_key_abc = f"{hash_name}/{midi_filename.replace('.mid', '.txt')}"
            s3_client.upload_file(abc_filename, S3_BUCKET, s3_key_abc)
            s3_link_abc = f"https://d2vdn8oszh8rp9.cloudfront.net/{s3_key_abc}"

            os.remove(temp_audio_file.name)
            os.remove(temp_midi_file.name)
            os.remove(abc_filename)

            return jsonify({
                "midi_file_link": s3_link_midi, 
                "abc_file_link": s3_link_abc,
                "track_name": nome_faixa
            }), 200

    except requests.RequestException as e:
        return {"error": f"Failed to download audio: {str(e)}"}, 400
    except subprocess.CalledProcessError as e:
        return {"error": f"midi2abc failed: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500
