import os
import re
import subprocess
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from pytube import YouTube
import demucs.api

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def download_and_convert_to_mp3(url):
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        video_title = re.sub(r'\s+', '-', yt.title)
        output_path = os.path.join('static', f'{video_title}.wav')
        subprocess.run(['ffmpeg', '-i', audio_stream.url, '-q:a', '0', '-map', 'a', output_path], check=True)
        return output_path
    except Exception as e:
        flash(f"Erro no baixar e converter: {str(e)}", 'error')
        return None

def separate_audio(filename):
    try:
        #htdemucs,htdemucs_ft,htdemucs_6s
        separador = demucs.api.Separator(model="htdemucs_6s")
        origem, separados = separador.separate_audio_file(filename)
        output_directory = "./static/separated/"
        os.makedirs(output_directory, exist_ok=True)
        order = ['vocals', 'bass', 'drums', 'guitar', 'piano', 'other']
        for stem, source in separados.items():
            file_path = f"{output_directory}{stem}.wav"
            demucs.api.save_audio(source, file_path, samplerate=separador.samplerate)
        sorted_files = [f"{output_directory}{stem}.wav" for stem in order if stem in separados]
        return [stem for stem in order if stem in separados]
    except Exception as e:
        flash(f"Erro ao separar áudio: {str(e)}", 'error')
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        file_path = os.path.join('static', filename)
        file.save(file_path)
        separated_files = separate_audio(file_path)
        if separated_files:
            return redirect(url_for('teste', filenames=separated_files))
    
    if 'url' in request.form:
        url = request.form['url']
        if not re.match(r'^(http(s)?://)?((w){3}.)?youtu(be|.be)?(\.com)?/.+', url):
            flash('Invalid YouTube URL', 'error')
            return redirect(request.url)
        mp3_file_path = download_and_convert_to_mp3(url)
        if mp3_file_path:
            separated_files = separate_audio(mp3_file_path)
            if separated_files:
                return redirect(url_for('teste', filenames=separated_files))
    
    return redirect(url_for('index'))

@app.route('/teste')
def teste():
    nomes_arquivos = request.args.getlist('filenames')
    return render_template('teste.html', filenames=nomes_arquivos)

if __name__ == '__main__':
    app.run(debug=True)