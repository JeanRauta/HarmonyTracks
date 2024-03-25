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
        # Separar faixas com o modelo htdemucs_ft
        separador_ft = demucs.api.Separator(model="htdemucs_ft")
        origem_ft, separados_ft = separador_ft.separate_audio_file(filename)
        output_directory_ft = "./static/separated/"
        os.makedirs(output_directory_ft, exist_ok=True)
        order_ft = ['vocals', 'bass', 'drums']
        for stem_ft, source_ft in separados_ft.items():
            if stem_ft in order_ft:
                file_path_ft = f"{output_directory_ft}{stem_ft}.wav"
                demucs.api.save_audio(source_ft, file_path_ft, samplerate=separador_ft.samplerate)
        
        # Separar faixas com o modelo htdemucs_6s
        separador_6s = demucs.api.Separator(model="htdemucs_6s")
        origem_6s, separados_6s = separador_6s.separate_audio_file(filename)
        order_6s = ['piano', 'guitar', 'other']
        for stem_6s, source_6s in separados_6s.items():
            if stem_6s in order_6s:
                file_path_6s = f"{output_directory_ft}{stem_6s}.wav"
                demucs.api.save_audio(source_6s, file_path_6s, samplerate=separador_6s.samplerate)
        
        # Retorna os caminhos dos arquivos separados
        return [f"{stem}.wav" for stem in order_ft], [f"{stem}.wav" for stem in order_6s]
    
    except Exception as e:
        flash(f"Erro ao separar áudio: {str(e)}", 'error')
        return [], []

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
        separated_files_ft, separated_files_6s = separate_audio(file_path)
        if separated_files_ft and separated_files_6s:
            return redirect(url_for('teste', filenames_ft=separated_files_ft, filenames_6s=separated_files_6s))
    
    if 'url' in request.form:
        url = request.form['url']
        if not re.match(r'^(http(s)?://)?((w){3}.)?youtu(be|.be)?(\.com)?/.+', url):
            flash('Invalid YouTube URL', 'error')
            return redirect(request.url)
        mp3_file_path = download_and_convert_to_mp3(url)
        if mp3_file_path:
            separated_files_ft, separated_files_6s = separate_audio(mp3_file_path)
            if separated_files_ft and separated_files_6s:
                return redirect(url_for('teste', filenames_ft=separated_files_ft, filenames_6s=separated_files_6s))
    
    return redirect(url_for('index'))

@app.route('/teste')
def teste():
    nomes_arquivos_ft = request.args.getlist('filenames_ft')
    nomes_arquivos_6s = request.args.getlist('filenames_6s')
    print(nomes_arquivos_ft + nomes_arquivos_6s)
    return render_template('teste.html', filenames=nomes_arquivos_ft + nomes_arquivos_6s)
    

if __name__ == '__main__':
    app.run(debug=True)
