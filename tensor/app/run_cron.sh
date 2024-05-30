#!/bin/bash

# Crear un archivo crontab
echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/root/bin" > /etc/cron.d/my_cron
echo "*/10 * * * * /usr/bin/python /app/script.py >> /var/log/cron.log 2>&1" > /etc/cron.d/my_cron
echo "*/30 * * * * /usr/bin/python /app/enviar_email.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/my_cron

# Aplicar permisos correctos
chmod 0644 /etc/cron.d/my_cron

# Aplicar crontab
crontab /etc/cron.d/my_cron

# Crear el archivo de log
touch /var/log/cron.log

# Iniciar cron
cron

# Mantener el contenedor en ejecución
tail -f /var/log/cron.log
	