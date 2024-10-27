bind = '0.0.0.0:5000'  
workers = 4
worker_class = 'sync'
timeout = 500

# Logs
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configurações de desempenho
preload_app = True
