from flask import Flask, request, send_file
from basic_pitch.inference import predict
import tempfile
import os

app = Flask(__name__)

@app.route('/convert_to_midi', methods=['POST'])
def convert_to_midi():
    if 'audio' not in request.files:
        return {"error": "No audio file provided"}, 400
    
    audio_file = request.files['audio']
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
        audio_file.save(temp_audio_file.name)
        
        model_output, midi_data, note_events = predict(temp_audio_file.name,  multiple_pitch_bends=False, melodia_trick=True)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as temp_midi_file:
            midi_data.write(temp_midi_file.name)
            
            return send_file(temp_midi_file.name, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
