import os
import openai
import base64
import logging
import requests
import cv2

# Inicializa el cliente de OpenAI con tu clave API
api_key = "sk-proj-190rkG6wXAe2DdgFpUHJT3BlbkFJdWpVPEeYrwJcY4TQLmRr"

# Configuración de logging
logging.basicConfig(filename="video_analysis_log.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def encode_frame(frame):
    """Codifica un frame a base64."""
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")

def analyze_image(base64_image):
    """Analiza una imagen utilizando la API de OpenAI."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "¿Qué está sucediendo en esta imagen? Proporcione el análisis en español."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    logging.debug(f"Respuesta de la API de OpenAI: {response.json()}")
    
    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json:
            return response_json['choices'][0]['message']['content']
        else:
            logging.error(f"La respuesta no contiene 'choices': {response_json}")
            return "Análisis no disponible para esta imagen."
    else:
        logging.error(f"Error en la llamada a la API: {response.status_code} {response.text}")
        return "Error al analizar la imagen."

def analyze_video(video_path):
    """Analiza un video extrayendo y procesando frames."""
    video = cv2.VideoCapture(video_path)
    frame_rate = int(video.get(cv2.CAP_PROP_FPS))
    frame_interval = frame_rate * 10  # Analiza un frame cada 10 segundos
    
    frame_number = 0
    analyses = []

    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        
        if frame_number % frame_interval == 0:
            base64_frame = encode_frame(frame)
            analysis = analyze_image(base64_frame)
            analyses.append(analysis)
            logging.info(f"Frame {frame_number}: {analysis}")
        
        frame_number += 1
    
    video.release()
    return analyses

def create_summary(analyses):
    """Crea un resumen de los resultados del análisis."""
    combined_analyses = " ".join(analyses)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": f"Resumen las siguientes observaciones en un solo párrafo en español: {combined_analyses}"
            }
        ],
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json:
            return response_json['choices'][0]['message']['content']
        else:
            logging.error(f"La respuesta no contiene 'choices': {response_json}")
            return "No se pudo generar un resumen."
    else:
        logging.error(f"Error en la llamada a la API: {response.status_code} {response.text}")
        return "Error al generar el resumen."

if __name__ == "__main__":
    video_path = 'D:\\pruebacollagevideos\\camera_6_2024_04_29_00_00__2024_04_29_07_59.mp4'  # Reemplaza con la ruta a tu video
    
    logging.info(f"Analizando video: {video_path}")
    analyses = analyze_video(video_path)
    
    logging.info("Creando resumen del video.")
    summary = create_summary(analyses)
    
    logging.info(f"Resumen del video: {summary}")
    print(summary)
