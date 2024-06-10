from basic_pitch.inference import predict_and_save

caminho_musica = 'teste2.mp3'
diretorio_saida = './'

predict_and_save(
    [caminho_musica],
    diretorio_saida,
    save_midi=True,
    sonify_midi=False,
    save_model_outputs=False,
    save_notes=False,
)