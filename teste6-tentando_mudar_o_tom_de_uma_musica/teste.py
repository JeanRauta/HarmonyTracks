import torch
import torchaudio
from torch_pitch_shift import pitch_shift, semitones_to_ratio

def change_pitch(input_file, output_file, shift_amount_semitones):
    # Carregar o arquivo de áudio usando torchaudio
    waveform, sample_rate = torchaudio.load(input_file)

    # Se o áudio for mono, adicione uma dimensão para representar os canais
    if waveform.dim() == 2:
        waveform = waveform.unsqueeze(0)

    # Converter a mudança de tom desejada de semitons para a proporção
    shift_ratio = semitones_to_ratio(shift_amount_semitones)

    # Aplicar a mudança de pitch
    shifted_waveform = pitch_shift(waveform, shift_ratio, sample_rate)

    # Salvar o arquivo de áudio resultante
    torchaudio.save(output_file, shifted_waveform.squeeze(0), sample_rate)

# Substitua 'input_audio.wav' pelo caminho do seu arquivo de áudio de entrada
input_audio_path = './teste.wav'

# Substitua 'output_audio_shifted.wav' pelo caminho do arquivo de áudio de saída desejado
output_audio_path = './output.wav'

# Definir a quantidade de mudança de pitch desejada em semitons
shift_amount_semitones = -5

# Chamar a função para mudar o tom
change_pitch(input_audio_path, output_audio_path, shift_amount_semitones)
