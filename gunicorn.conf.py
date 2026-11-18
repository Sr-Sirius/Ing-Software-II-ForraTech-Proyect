# gunicorn.conf.py
# Gunicorn carga este archivo automáticamente cuando se ejecuta desde la
# raíz del proyecto (por ejemplo, el start command de Render
# "gunicorn run:app"). Los argumentos escritos en el start command tienen
# prioridad sobre estos valores.
#
# Render define la variable PORT y Gunicorn la usa para escuchar en
# 0.0.0.0:$PORT, así que no se configura "bind" aquí.

# Un solo proceso: el plan gratuito tiene 512 MB y los modelos de ML ocupan
# memoria. Varios hilos permiten atender el sondeo (polling) del chat
# mientras otra petición está en curso.
workers = 1
worker_class = "gthread"
threads = 8

# Tiempo máximo por petición (las páginas de modelos pueden tardar).
timeout = 120
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"
