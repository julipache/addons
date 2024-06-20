FROM python:3.9-slim

# Instala ffmpeg y las dependencias
RUN apt-get update && apt-get install -y ffmpeg
	
	


# Crear un enlace simbólico de python a python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# Instalar dependencias necesarias
RUN pip install flask websockets

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el directorio de la aplicación
COPY ./app /app

EXPOSE 8099
EXPOSE 8081
EXPOSE 8082

# Comando para ejecutar el script de configuración de cron
CMD ["python", "visor.py"]
