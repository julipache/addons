import numpy as np
import os
import shutil
import csv
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import logging
from datetime import datetime

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directorios
input_directory = '/media/frigate/clips/recortado'
output_directory = '/media/frigate/clips/clasificado'
doubtful_directory = os.path.join(output_directory, 'dudosos')
log_file_path = '/media/frigate/clips/predicciones_log.csv'

# Crear directorios si no existen
os.makedirs(output_directory, exist_ok=True)
os.makedirs(doubtful_directory, exist_ok=True)

# Cargar el modelo entrenado
model_path = '/media/mi_modelo_entrenado.keras'
model = load_model(model_path)
logging.info("Model loaded successfully")

# Etiquetas de clases
class_labels = {0: 'coco', 1: 'pina', 2: 'pollo', 3: 'ray', 4: 'snape'}

# Función para cargar y preprocesar una imagen
def load_and_prepare_image(img_path, target_size=(224, 224)):
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return img_array

# Función para predecir la clase de una imagen y moverla al directorio correspondiente
def predict_and_classify_image(img_path, log_writer):
    img_array = load_and_prepare_image(img_path)
    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    predicted_class_name = class_labels[predicted_class_index]
    confidence = np.max(predictions) * 100

    logging.info(f"Processed {img_path} - Predicted: {predicted_class_name}, Confidence: {confidence:.2f}%")

    if confidence < 70:  # Umbral de confianza para considerar una imagen como "dudosa"
        target_folder = doubtful_directory
    else:
        target_folder = os.path.join(output_directory, predicted_class_name)
    
    os.makedirs(target_folder, exist_ok=True)
    shutil.move(img_path, os.path.join(target_folder, os.path.basename(img_path)))

    # Escribir la predicción en el log
    log_writer.writerow([os.path.basename(img_path), predicted_class_name, confidence])

# Abrir el archivo CSV para guardar el log de predicciones
with open(log_file_path, mode='w', newline='') as log_file:
    log_writer = csv.writer(log_file)
    log_writer.writerow(['Image', 'Predicted Class', 'Confidence'])

    # Procesar y clasificar imágenes en el directorio de entrada
    for root, dirs, files in os.walk(input_directory):
        for filename in files:
            if filename.endswith((".png", ".jpg", ".jpeg")):
                img_path = os.path.join(root, filename)
                predict_and_classify_image(img_path, log_writer)

logging.info("Image classification completed")
