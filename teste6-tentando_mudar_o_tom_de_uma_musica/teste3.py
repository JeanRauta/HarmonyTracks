from pydub import AudioSegment
from pydub.playback import play

def aumentar_velocidade_sem_alterar_tom(arquivo_entrada, fator_aumento, arquivo_saida):
    # Carregar o áudio de entrada
    audio = AudioSegment.from_file(arquivo_entrada)

    # Aumentar a velocidade sem alterar o tom
    audio_aumentado = audio.speedup(playback_speed=fator_aumento)

    # Salvar o áudio aumentado
    audio_aumentado.export(arquivo_saida, format="wav")

    # Reproduzir o áudio aumentado (opcional)
    play(audio_aumentado)

# Exemplo de uso
arquivo_entrada = "./teste.wav"
fator_aumento = 3  # Ajuste o fator conforme necessário (1.0 mantém a velocidade original)
arquivo_saida = "./arquivo.wav"

aumentar_velocidade_sem_alterar_tom(arquivo_entrada, fator_aumento, arquivo_saida)
