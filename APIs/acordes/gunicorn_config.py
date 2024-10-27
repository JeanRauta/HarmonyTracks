bind = '0.0.0.0:5002'  
workers = 4
worker_class = 'sync'
timeout = 30

# Logs
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configurações de desempenho
preload_app = True
