from chord_extractor.extractors import Chordino

chordino = Chordino()

caminho_da_musica = "./teste.wav"

acordes = chordino.extract(caminho_da_musica)

for acorde in acordes:
    print(acorde.chord)