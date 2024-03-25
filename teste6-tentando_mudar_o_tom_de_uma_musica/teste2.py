from pydub import AudioSegment
from pydub.playback import play

def alterar_tom_sem_alterar_velocidade(arquivo_entrada, semitons, arquivo_saida):
    # Carregar o áudio de entrada
    audio = AudioSegment.from_file(arquivo_entrada)

    # Alterar o tom sem alterar a velocidade
    audio_alterado = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * (2 ** (semitons / 12.0)))
    })

    # Salvar o áudio alterado
    audio_alterado.export(arquivo_saida, format="wav")

    # Reproduzir o áudio alterado (opcional)
    play(audio_alterado)

# Exemplo de uso
arquivo_entrada = "./teste.wav"
semitons = 2  # Ajuste o valor conforme necessário (positivo para aumentar o tom, negativo para diminuir)
arquivo_saida = "./arquivo.wav"

alterar_tom_sem_alterar_velocidade(arquivo_entrada, semitons, arquivo_saida)
