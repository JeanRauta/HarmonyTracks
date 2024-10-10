from flask import Flask, request, send_file
import os
import tempfile
from omnizart.music import app as music_app

app = Flask(__name__)

@app.route('/convert-to-midi', methods=['POST'])
def convert_to_midi():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        file.save(temp_audio_file.name) 
        temp_audio_file.flush()

        midi_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mid").name

        music_app.transcribe(temp_audio_file.name , output=midi_path)

        return send_file(
            midi_path,
            as_attachment=True,  
            attachment_filename=os.path.basename(midi_path),  
            mimetype='audio/midi'
        )

if __name__ == '__main__':
    app.run(debug=True)
