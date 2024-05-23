FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Instalar dependencias necesarias
RUN pip install tensorflow numpy pillow opencv-python

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el directorio de la aplicación
COPY ./app /app

# Comando para ejecutar el script
CMD ["python", "pruebamsiva.py"]
