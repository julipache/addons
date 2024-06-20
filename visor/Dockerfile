FROM python:3.9-slim

# Copia el script en el contenedor
COPY visor.py /app/visor.py

# Instala las dependencias
RUN pip install flask opencv-python

# Define el puerto en el que se ejecutará la aplicación
EXPOSE 5000

# Comando por defecto para ejecutar el script
CMD ["python", "/app/visor.py"]
