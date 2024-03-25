from flask import Flask, request, render_template, redirect
import os
import shutil
import demucs.api

app = Flask(__name__)

def process_audio(file_path):
    separator = demucs.api.Separator()
    origin, separated = separator.separate_audio_file(file_path)

    output_directory = "./static/"

    processed_files = []

    os.remove(file_path)

    for stem, source in separated.items():
        file_name = f"{stem}.wav"
        file_path = os.path.join(output_directory, file_name)
        demucs.api.save_audio(source, file_path, samplerate=separator.samplerate)
        processed_files.append(file_name)
    return processed_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)


    if file:
        file_path = os.path.join('./uploads', 'teste.mp3')
        file.save(file_path)

        processed_files = process_audio(file_path)
        return render_template('result.html', processed_files=processed_files)

if __name__ == '__main__':
    app.run(debug=True)