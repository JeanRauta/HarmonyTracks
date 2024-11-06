# Inicia o gateway
echo "Iniciando o servidor Gateway..."
source /home/eu/miniconda3/etc/profile.d/conda.sh
conda activate main
gnome-terminal -- bash -c "cd /home/eu/Documentos/HarmonyTracks/APIs/main && gunicorn -c gunicorn_config.py app:app; exec bash"

# Inicia a API de separação de faixas
echo "Iniciando o servidor de separação de faixas..."
source /home/eu/miniconda3/etc/profile.d/conda.sh
conda activate envht
gnome-terminal -- bash -c "cd /home/eu/Documentos/HarmonyTracks/APIs/separacao && gunicorn -c gunicorn_config.py app:app; exec bash"

# Inicia a API de identificação de acordes
echo "Iniciando o servidor de identificação de acordes..."
source /home/eu/miniconda3/etc/profile.d/conda.sh
conda activate chords
gnome-terminal -- bash -c "cd /home/eu/Documentos/HarmonyTracks/APIs/acordes && gunicorn -c gunicorn_config.py app:app; exec bash"

# Inicia a API de conversão para MIDI
echo "Iniciando o servidor de conversão para MIDI..."
source /home/eu/miniconda3/etc/profile.d/conda.sh
conda activate basic
gnome-terminal -- bash -c "cd /home/eu/Documentos/HarmonyTracks/APIs/midi/basic-pitch && gunicorn -c gunicorn_config.py app:app; exec bash"

echo "Todos os servidores foram iniciados."
