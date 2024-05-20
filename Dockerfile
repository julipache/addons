FROM python:3.8-slim

# Instalar dependencias necesarias
RUN pip install tensorflow numpy pillow

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el directorio de la aplicación
COPY ./app /app

# Comando para ejecutar el script
CMD ["python", "pruebamsiva.py"]
