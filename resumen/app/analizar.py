import os
import openai
import base64
import smtplib
import requests
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta

import cv2

def crear_video_por_gato(imagenes_por_gato, output_directory, fps=1):
    """
    Crea videos separados por gato a partir de listas de imágenes.

    Args:
        imagenes_por_gato (dict): Diccionario con nombres de gatos como claves y listas de rutas de imágenes como valores.
        output_directory (str): Directorio donde se guardarán los videos.
        fps (int): Fotogramas por segundo para el video.
    """
    for gato, imagenes in imagenes_por_gato.items():
        if not imagenes:
            logging.error(f"No hay imágenes para crear el video de {gato}.")
            continue

        # Leer la primera imagen para obtener el tamaño del video
        frame = cv2.imread(imagenes[0])
        height, width, layers = frame.shape
        size = (width, height)

        # Crear el directorio de salida si no existe
        os.makedirs(output_directory, exist_ok=True)

        # Inicializar el objeto de escritura de video
        video_path = os.path.join(output_directory, f"{gato}.avi")
        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'DIVX'), fps, size)

        for imagen in imagenes:
            frame = cv2.imread(imagen)
            out.write(frame)

        out.release()
        logging.info(f"Video de {gato} guardado en {video_path}")



def es_reciente(file_path, horas=8):
    """
    Verifica si el archivo fue creado en las últimas 'horas' horas.
    
    Args:
        file_path (str): La ruta del archivo.
        horas (int): Número de horas para verificar.
        
    Returns:
        bool: True si el archivo fue creado en las últimas 'horas' horas, de lo contrario False.
    """
    tiempo_limite = datetime.now() - timedelta(hours=horas)
    fecha_creacion = datetime.fromtimestamp(os.path.getctime(file_path))
    return fecha_creacion > tiempo_limite

# Initialize OpenAI client
api_key = "sk-proj-MugjWhRd0NQwiXtq0jxiT3BlbkFJqvgpY48QFW6lVz56FvnO"

# Configure logging
logging.basicConfig(filename="analysis_log.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def encode_image(image_path):
    """Encodes an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image(image_path):
    """Analyzes an image using the OpenAI API."""
    base64_image = encode_image(image_path)
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
                        "text": "¿Qué está haciendo el gato en esta imagen? Proporcione el análisis en español."
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
    logging.debug(f"OpenAI API response: {response.json()}")
    return response.json()['choices'][0]['message']['content']

def analyze_images_in_directory(directory_path, originales_path):
    """Analyzes all images in the given directory and its subdirectories."""
    results = {}
    image_count = 0
    for root, dirs, files in os.walk(directory_path):
        logging.info(f"Exploring directory: {root}")
        for dir_name in dirs:
            cat_dir_path = os.path.join(root, dir_name)
            logging.info(f"Found directory: {cat_dir_path}")
            results[dir_name] = {}
            for sub_root, sub_dirs, sub_files in os.walk(cat_dir_path):
                logging.info(f"Exploring subdirectory: {sub_root}")
                for sub_dir in sub_dirs:
                    date_dir_path = os.path.join(sub_root, sub_dir)
                    logging.info(f"Found date directory: {date_dir_path}")
                    results[dir_name][sub_dir] = []
                    file_count = 0
                    for filename in os.listdir(date_dir_path):
                        logging.info(f"Checking file: {filename}")
                        if filename.endswith(('.png', '.jpg', '.jpeg')):
                            image_path = os.path.join(date_dir_path, filename)
                            logging.info(f"Found image file: {image_path}")
                            original_image_name = filename.replace("clean_crop", "clean_detection")
                            original_image_path = os.path.join(originales_path, dir_name, original_image_name)
                            logging.info(f"Looking for original image: {original_image_path}")
                            if os.path.exists(original_image_path):
                                analysis = analyze_image(original_image_path)
                                logging.info(f"Using original image for analysis: {original_image_path}")
                            else:
                                analysis = analyze_image(image_path)
                                logging.info(f"Using cropped image for analysis: {image_path}")
                            results[dir_name][sub_dir].append(analysis)
                            image_count += 1
                            file_count += 1
                            logging.info(f"Analyzed image: {image_path}")
                    logging.info(f"Total images in {date_dir_path}: {file_count}")
    logging.info(f"Total images analyzed: {image_count}")
    return results

def create_summary(analysis_results):
    """Creates an organic summary of the analysis results for each cat."""
    summary_texts = []
    for cat_name, dates in analysis_results.items():
        cat_summaries = []
        for date, analyses in dates.items():
            cat_summaries.extend(analyses)
        
        # Create a single summary for all analyses of this cat
        combined_analyses = " ".join(cat_summaries)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": f"Resumen las siguientes observaciones sobre el gato {cat_name} en un solo párrafo en español: {combined_analyses}"
                }
            ],
            "max_tokens": 300
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        summary = response.json()['choices'][0]['message']['content']
        summary_texts.append(f"{cat_name}:\n{summary}\n")
    
    final_summary = "\n".join(summary_texts)
    return final_summary

# Configuración de correo electrónico
def send_email(subject, body, attachments):
    sender_email = "75642e001@smtp-brevo.com"
    receiver_email = "julioalberto85@gmail.com"
    password = "8nP5LXfVT1tmvCgW"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    for file_path in attachments:
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(file_path)}",
            )
            message.attach(part)
        except Exception as e:
            logging.error(f"Error attaching file {file_path}: {str(e)}")

    try:
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.close()
        logging.info("Email sent successfully")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error sending email: {str(e)}")
    except Exception as e:
        logging.error(f"General error sending email: {str(e)}")

if __name__ == "__main__":
    directory_path = '/media/frigate/clasificado'
    originales_path = '/media/frigate/originales'
    
    images = list_images(directory_path)
    
    analysis_results = {}
    original_images_for_video = {gato: [] for gato in images.keys()}
    
    for cat_name, cat_images in images.items():
        logging.info(f"Analyzing images for cat: {cat_name}")
        cat_results = []
        for image in cat_images:
            if es_reciente(image, horas=8):
                logging.info(f"Analyzing image: {image}")
                original_image_path = find_original_image(image, originales_path)
                if original_image_path:
                    descripcion = analyze_image(original_image_path)
                    original_images_for_video[cat_name].append(original_image_path)
                else:
                    descripcion = analyze_image(image)
                    original_images_for_video[cat_name].append(image)
                logging.info(f"Analysis result: {descripcion}")
                
                #gato_nuevo = verificar_y_recategorizar(image, descripcion, gato_caracteristicas)
                #if gato_nuevo != cat_name:
                #    logging.info(f"Recategorizing {image} from {cat_name} to {gato_nuevo}")
                #    mover_a_carpeta_correcta(image, gato_nuevo)
                
                cat_results.append(descripcion)
        analysis_results[cat_name] = cat_results

    email_body = create_summary(analysis_results)
    chronology = create_chronology(images)
    chronology_text = format_chronology(chronology)

    full_email_body = email_body + "\nCronología de Movimientos:\n" + chronology_text

    # Crear los videos por gato
    output_video_directory = '/media/frigate/videos_resumen'
    crear_video_por_gato(original_images_for_video, output_video_directory)

    # Adjuntar los videos de cada gato
    video_files = [os.path.join(output_video_directory, f"{gato}.avi") for gato in original_images_for_video.keys()]

    send_email(
        subject="Resultados del Análisis de Imágenes de Gatos",
        body=full_email_body,
        attachments=["analysis_log.log"] + video_files
    )
