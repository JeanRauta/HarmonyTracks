from flask import Flask, request, jsonify
from basic_pitch.inference import predict
import tempfile
import os
import hashlib
import boto3
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)



S3_BUCKET = 'htracks'

@app.route('/convert_to_midi', methods=['POST'])
def convert_to_midi():
    if 'audio_url' not in request.json:
        return {"error": "No audio URL provided"}, 400
    
    audio_url = request.json['audio_url']
    
    try:
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()  

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_audio_file.write(chunk)
        
        model_output, midi_data, note_events = predict(temp_audio_file.name, multiple_pitch_bends=False, melodia_trick=True)
        
        hash_name = hashlib.sha256(audio_url.encode()).hexdigest()
        
        midi_filename = f"{os.path.basename(audio_url).split('.')[0]}.mid"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as temp_midi_file:
            midi_data.write(temp_midi_file.name)

            s3_key = f"{hash_name}/{midi_filename}"  
            s3_client.upload_file(temp_midi_file.name, S3_BUCKET, s3_key)

            s3_link = f"https://d2vdn8oszh8rp9.cloudfront.net/{s3_key}"

            return jsonify({"midi_file_link": s3_link}), 200

    except requests.RequestException as e:
        return {"error": str(e)}, 400
