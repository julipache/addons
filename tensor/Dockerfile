FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

# Instalar dependencias necesarias
RUN pip install tensorflow numpy pillow opencv-python opencv-python-headless sendgrid

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el directorio de la aplicación
COPY ./app /app



RUN chmod +x /app/run_cron.sh

CMD ["/app/run_cron.sh"]

