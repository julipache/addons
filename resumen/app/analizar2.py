import os
import logging
import json
import base64
from datetime import datetime, timedelta
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import cv2

# Configuración del log
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Leer configuración externa (credenciales)
with open('/data/options.json', 'r') as f:
    options = json.load(f)

openai_api_key = options.get('openai_api_key')
sender_email = "75642e001@smtp-brevo.com"
password = options.get('emailpass')
destinatarios = ["julioalberto85@gmail.com", "nuriagiadas@gmail.com"]

# Directorios
directorio_base = '/media/frigate/clasificado'
directorio_originales = '/media/frigate/originales'
directorio_ezviz = '/config/ezviz_gatitos'
directorio_media_ezviz = '/media/ezviz_gatitos'

def es_reciente(file_path, horas=24):
    return datetime.fromtimestamp(os.path.getmtime(file_path)) > datetime.now() - timedelta(hours=horas)

def cargar_imagenes_originales():
    imagenes = {}
    for root, _, files in os.walk(directorio_originales):
        for file in files:
            if "-clean" in file:
                nombre_base = file.split('-clean')[0]
                imagenes[nombre_base] = os.path.join(root, file)
    return imagenes

def buscar_imagen_original(nombre_crop, imagenes_originales):
    base = nombre_crop.split('_crop')[0]
    return imagenes_originales.get(base)

def resumen_gatos():
    resumen, fotos, videos = {}, {}, {}
    imagenes_originales = cargar_imagenes_originales()
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
            resumen[gato].sort()
            fotos[gato].sort(key=lambda x: os.path.getmtime(x))
    return resumen, fotos, videos

def crear_video_ezviz():
    imagenes = sorted([
        os.path.join(directorio_ezviz, img)
        for img in os.listdir(directorio_ezviz)
        if img.lower().endswith('.jpg')
    ], key=lambda x: os.path.getmtime(x))
    if not imagenes:
        return None

    os.makedirs(directorio_media_ezviz, exist_ok=True)
    frame = cv2.imread(imagenes[0])
    height, width, _ = frame.shape
    salida = os.path.join(directorio_media_ezviz, "ezviz_gatitos.mp4")
    out = cv2.VideoWriter(salida, cv2.VideoWriter_fourcc(*'mp4v'), 1, (width, height))
    for img in imagenes:
        frame = cv2.imread(img)
        if frame is not None:
            out.write(frame)
    out.release()
    return salida

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analizar_imagen_con_openai(imagen_path, client):
    base64_image = encode_image(imagen_path)
    prompt = [
        {"role": "system", "content": "Eres un experto en identificar gatos, colores, otros animales o personas en imágenes."},
        {"role": "user", "content": [
            {"type": "text", "text": "Describe todos los animales visibles (gatos, zorros, personas, etc.) y sus colores."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,[imagen codificada omitida]"}}
        ]}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt,
            max_tokens=500,
        )
        resultado = response.choices[0].message.content
        logging.debug(f"Respuesta OpenAI para {imagen_path}: {resultado}")
        return resultado
    except Exception as e:
        logging.error(f"Error durante la llamada a OpenAI con {imagen_path}: {e}")
        return "(error en análisis de imagen)"

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

        if fotos.get(gato):
            html += "<h3>Fotos:</h3>"
            for file_path in fotos[gato][:5]:
                cid = os.path.basename(file_path)
                html += f'<img src="cid:{cid}" style="max-width:200px; margin:5px;"/>'

    html += f"<h2>Resumen de análisis de EZVIZ:</h2><pre>{resumen_openai}</pre>"
    html += f'<p><a href="https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Fezviz_gatitos">Ver vídeo de EZVIZ</a></p>'
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

if __name__ == "__main__":
    logging.info("Generando resumen...")
    resumen, fotos, videos_gatos = resumen_gatos()

    logging.info("Creando video de EZVIZ...")
    video_ezviz_path = crear_video_ezviz()
    resumen_openai = ""
    if video_ezviz_path:
        client = OpenAI(api_key=openai_api_key)
        logging.info("Analizando imágenes de EZVIZ con OpenAI...")
        ezviz_images = sorted([
            os.path.join(directorio_ezviz, f)
            for f in os.listdir(directorio_ezviz)
            if f.lower().endswith('.jpg')
        ], key=lambda x: os.path.getmtime(x))

        analisis_ezviz = []
        for img_path in ezviz_images[:10]:
            try:
                analisis = analizar_imagen_con_openai(img_path, client)
                analisis_ezviz.append(analisis)
            except Exception as e:
                logging.error(f"Error analizando imagen EZVIZ {img_path}: {e}")

        resumen_openai = "\n".join(analisis_ezviz)

    if any(resumen.values()):
        cuerpo_email = crear_cuerpo_email(resumen, resumen_openai, fotos)
        send_email("Resumen de actividad de gatos", cuerpo_email, fotos, destinatarios)
