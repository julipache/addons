	FROM python:3.9-slim

	# Instala ffmpeg y las dependencias
	RUN apt-get update && \
		apt-get install -y --no-install-recommends \
		build-essential \
		libglib2.0-0 \
		libsm6 \
		libxext6 \
		libxrender1 \
		libopencv-dev \
		ffmpeg && \
		pip install --no-cache-dir \
		openai \
		requests \
		opencv-python-headless \
		smtplib
		
		


	# Crear un enlace simbólico de python a python3
	RUN ln -s /usr/bin/python3 /usr/bin/python

	# Instalar dependencias necesarias
	RUN pip install --no-cache-dir \
		openai \
		requests \
		opencv-python-headless \
		Flask \
		websockets


	# Establecer el directorio de trabajo
	WORKDIR /app

	# Copiar el directorio de la aplicación
	COPY ./app /app

	EXPOSE 8099
	EXPOSE 8081
	EXPOSE 8082

	# Comando para ejecutar el script de configuración de cron
	CMD ["python", "analizar2.py"]
