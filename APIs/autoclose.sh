
echo "Fechando todos os servidores Gunicorn..."

# Matar processos do Gunicorn
pkill -f 'gunicorn' 

echo "Todos os servidores foram fechados."
