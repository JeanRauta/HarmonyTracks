from chorder import Dechorder
from miditoolkit import MidiFile

def identificar_acordes(caminho_arquivo):
    # Carregar arquivo MIDI
    midi_file = MidiFile(caminho_arquivo)
    
    # Extrair acordes
    chords = Dechorder.dechord(midi_file)
    
    # Exibir acordes identificados
    print("Acordes identificados:")
    for chord in chords:
        print(chord)

if __name__ == "__main__":
    caminho_arquivo_midi = "titanic.mid"
    identificar_acordes(caminho_arquivo_midi)
