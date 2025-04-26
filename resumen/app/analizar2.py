import os
import shutil
import logging
import time
import base64
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import cv2
from openai import OpenAI
import json


# Configuracion de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Parametros generales
directorio_base = '/media/frigate/clasificado'
directorio_originales = '/media/frigate/originales'
directorio_videos = '/media/frigate/videos'
directorio_ezviz = '/config/ezviz_gatitos'
directorio_media_ezviz = '/media/ezviz_gatitos'
sender_email = "75642e001@smtp-brevo.com"
password = "8nP5LXfVT1tmvCgW"
destinatarios = ["julioalberto85@gmail.com", "nuriagiadas@gmail.com"]
with open('/data/options.json', 'r') as f:
    options = json.load(f)

openai_api_key = options.get('openai_api_key')

# Utilidades

def es_reciente(file_path, horas=24):
    tiempo_limite = datetime.now() - timedelta(hours=horas)
    return datetime.fromtimestamp(os.path.getmtime(file_path)) > tiempo_limite

def cargar_imagenes_originales(directorio):
    imagenes = {}
    for root, _, files in os.walk(directorio):
        for file in files:
            if "-clean" in file:
                nombre_base = file.split('-clean')[0]
                imagenes[nombre_base] = os.path.join(root, file)
    return imagenes

def buscar_imagen_original(nombre_crop, imagenes_originales):
    base = nombre_crop.split('_crop')[0]
    return imagenes_originales.get(base)

def crear_video(nombre, imagenes, salida):
    if not imagenes:
        return None
    os.makedirs(salida, exist_ok=True)
    imagenes.sort(key=lambda x: os.path.getmtime(x))
    frame = cv2.imread(imagenes[0])
    if frame is None:
        logging.error(f"No se puede leer {imagenes[0]}")
        return None
    height, width, _ = frame.shape
    video_path = os.path.join(salida, f"{nombre}.mp4")
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 1, (width, height))
    for img_path in imagenes:
        frame = cv2.imread(img_path)
        if frame is not None:
            out.write(frame)
    out.release()
    return video_path

def resumen_gatos():
    resumen, fotos, videos = {}, {}, {}
    imagenes_originales = cargar_imagenes_originales(directorio_originales)
    for gato in os.listdir(directorio_base):
        path_gato = os.path.join(directorio_base, gato)
        if os.path.isdir(path_gato) and gato != "dudosos":
            resumen[gato], fotos[gato], videos[gato] = [], [], []
            for imagen in os.listdir(path_gato):
                path_imagen = os.path.join(path_gato, imagen)
                if os.path.isfile(path_imagen) and es_reciente(path_imagen):
                    camara = imagen.split('-')[0]
                    fecha = datetime.fromtimestamp(os.path.getmtime(path_imagen))
                    resumen[gato].append((fecha, camara))
                    original = buscar_imagen_original(imagen, imagenes_originales)
                    fotos[gato].append(original if original else path_imagen)
                    videos[gato].append(original if original else path_imagen)
            resumen[gato].sort()
            fotos[gato].sort(key=lambda x: os.path.getmtime(x))
    return resumen, fotos, videos

def crear_video_ezviz():
    imagenes = sorted([os.path.join(directorio_ezviz, img) for img in os.listdir(directorio_ezviz) if img.lower().endswith('.jpg')], key=lambda x: os.path.getmtime(x))
    return crear_video("ezviz_gatitos", imagenes, directorio_videos) if imagenes else None

def mover_video_a_media(video_path):
    os.makedirs(directorio_media_ezviz, exist_ok=True)
    destino = os.path.join(directorio_media_ezviz, "ezviz_gatitos.mp4")
    shutil.copy(video_path, destino)
    logging.info(f"Vídeo movido a {destino}")
    return destino

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analizar_imagen_con_openai(imagen_path, client):
    base64_image = encode_image(imagen_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Eres un experto en identificar gatos, colores, otros animales o personas en imágenes."},
            {"role": "user", "content": [
                {"type": "text", "text": "Describe todos los animales visibles (gatos, zorros, personas, etc.) y sus colores."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content

def crear_cuerpo_email(resumen, resumen_openai, fotos):
    html = """<html><body><h1>Resumen de Gatos Detectados en las Últimas 24 Horas</h1>"""
    for gato, detecciones in resumen.items():
        html += f"<h2>{gato}</h2>"
        if detecciones:
            html += "<ul>"
            for fecha, camara in detecciones:
                html += f"<li>{camara} a las {fecha.strftime('%Y-%m-%d %H:%M:%S')}</li>"
            html += "</ul>"
        else:
            html += f"<p>{gato}: sin actividad reciente</p>"

        # Añadir fotos de cada gato justo después
        if fotos.get(gato):
            html += "<h3>Fotos:</h3>"
            for file_path in fotos[gato][:5]:
                cid = os.path.basename(file_path)
                html += f'<img src="cid:{cid}" style="max-width:200px; margin:5px;"/>'

    html += f"<h2>Resumen de análisis de imágenes:</h2><p>{resumen_openai}</p>"
    html += """</body></html>"""
    return html

def send_email(subject, body, fotos, destinatarios):
    message = MIMEMultipart('related')
    message['From'] = sender_email
    message['To'] = ", ".join(destinatarios)
    message['Subject'] = subject

    message_alt = MIMEMultipart('alternative')
    message.attach(message_alt)
    message_alt.attach(MIMEText(body, 'html'))

    for paths in fotos.values():
        for file_path in paths[:5]:
            try:
                with open(file_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f"<{os.path.basename(file_path)}>")
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(file_path))
                    message.attach(img)
            except Exception as e:
                logging.error(f"Error adjuntando imagen {file_path}: {e}")

    try:
        server = smtplib.SMTP('smtp-relay.brevo.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, destinatarios, message.as_string())
        server.quit()
        logging.info("Email enviado correctamente")
    except Exception as e:
        logging.error(f"Error enviando email: {e}")
        logging.info("Email enviado correctamente")
    except Exception as e:
        logging.error(f"Error enviando email: {e}")

def send_email_video(subject, destinatarios, link_video):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = ", ".join(destinatarios)
    message['Subject'] = subject
    body = f"""
    <html><body>
    <h1>Vídeo de movimiento EZVIZ</h1>
    <p>Puedes ver el vídeo de las últimas 24 horas en el siguiente enlace:</p>
    <a href="{link_video}">Ver vídeo</a>
    </body></html>
    """
    message.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp-relay.brevo.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, destinatarios, message.as_string())
        server.quit()
        logging.info("Email del vídeo EZVIZ enviado correctamente")
    except Exception as e:
        logging.error(f"Error enviando email de vídeo EZVIZ: {e}")

# Ejecución principal
if __name__ == "__main__":
    logging.info("Generando resumen...")
    resumen, fotos, videos_gatos = resumen_gatos()
    if any(resumen.values()):
        client = OpenAI(api_key=openai_api_key)
        logging.info("Analizando imágenes con OpenAI...")
        analisis_imagenes = []
        for paths in fotos.values():
            for img_path in paths[:5]:
                try:
                    analisis = analizar_imagen_con_openai(img_path, client)
                    analisis_imagenes.append(analisis)
                except Exception as e:
                    logging.error(f"Error analizando imagen {img_path}: {e}")
        resumen_openai = " ".join(analisis_imagenes)

        logging.info("Creando videos de gatos...")
        for gato, imagenes in videos_gatos.items():
            crear_video(gato, imagenes, directorio_videos)

        logging.info("Creando video de EZVIZ...")
        video_ezviz_path = crear_video_ezviz()
        if video_ezviz_path:
            mover_video_a_media(video_ezviz_path)
            link_video = "https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Fezviz_gatitos"
