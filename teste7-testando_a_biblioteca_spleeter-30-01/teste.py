import subprocess
import os

# Instale as dependências necessárias usando o Conda
# Certifique-se de ter o Conda instalado em seu sistema
# Execute os seguintes comandos no terminal (pode ser no VS Code terminal):
# conda install -c conda-forge ffmpeg libsndfile
# pip install spleeter

# Caminho para o arquivo de áudio que você deseja separar
audio_file_path = "./sweet.mp3"

# Caminho para o diretório de saída
output_directory = "./"

# Comando para separar o áudio usando Spleeter
spleeter_command = f"spleeter separate -p spleeter:4stems -o {output_directory} {audio_file_path}"

# Execute o comando usando subprocess
subprocess.run(spleeter_command, shell=True)

# Verifique o diretório de saída para os arquivos separados
separated_files = os.listdir(output_directory)
print("Arquivos Separados:", separated_files)
