import re
from pytube import YouTube
import subprocess

def download_and_convert_to_mp3(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()

    video_title = re.sub(r'\s+', '-', yt.title)

    subprocess.run(['ffmpeg', '-i', audio_stream.url, '-q:a', '0', '-map', 'a', f'{video_title}.mp3'])

if __name__ == "__main__":
    url = input("Insira a URL do vídeo que deseja converter para MP3: ")
    download_and_convert_to_mp3(url)
