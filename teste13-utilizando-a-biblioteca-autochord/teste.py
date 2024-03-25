import autochord

# Substitua 'caminho/para/sua/musica.wav' pelo caminho real para o arquivo de áudio da sua música
arquivo_audio = './testen.mp3'

# Substitua 'caminho/para/salvar/suas/labels.lab' pelo caminho onde você deseja salvar o arquivo de saída de acordes
arquivo_labels = './teste.lab'

# Realiza a análise de acordes
autochord.recognize(arquivo_audio, lab_fn=arquivo_labels)

print("Análise de acordes concluída com sucesso!")
