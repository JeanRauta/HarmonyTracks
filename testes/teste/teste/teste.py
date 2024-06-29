import essentia
import essentia.standard as es

# Função para extrair a melodia e salvar como MIDI
def extrair_melodia_audio_para_midi(audio_file, output_midi_file):
    # Carregar o áudio
    loader = es.MonoLoader(filename=audio_file)
    audio = loader()

    # Inicializar o algoritmo MusicExtractor
    extractor = es.MusicExtractor()

    # Definir parâmetros para extração de melodia
    parameters = {
        "algorithm": "default",
        "method": "melodia"
    }

    # Extrair a melodia
    extractor_output = extractor(audio, parameters=parameters)
    melodia = extractor_output["melody"]

    # Converter a melodia para um formato que pode ser exportado como MIDI
    midi_notes = es.arrayToMIDI(melodia)

    # Salvar o MIDI
    es.MIDIFileWriter()(midi_notes, output_midi_file)

    print(f"Melodia extraída e salva como MIDI em {output_midi_file}")

# Exemplo de uso
if __name__ == "__main__":
    audio_file = "./teste.wav"
    output_midi_file = "melodia_extraida.mid"

    extrair_melodia_audio_para_midi(audio_file, output_midi_file)
