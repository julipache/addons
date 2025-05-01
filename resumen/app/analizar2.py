import os
import time
import cv2
import smtplib
import json
import base64
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from openai import OpenAI

logging.basicConfig(level=logging.DEBUG)

def es_reciente(file_path, horas=24):
    tiempo_limite = datetime.now() - timedelta(hours=horas)
    fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(file_path))
    return fecha_modificacion > tiempo_limite

def obtener_camara_de_imagen(nombre_imagen):
    return nombre_imagen.split('-')[0]

def cargar_imagenes_originales(directorio_originales):
    imagenes_originales = {}
    for root, _, files in os.walk(directorio_originales):
        for file in files:
            if "-clean" in file:
                nombre_base = file.split('-clean')[0]
                imagenes_originales[nombre_base] = os.path.join(root, file)
    return imagenes_originales

def buscar_imagen_original(nombre_imagen_recortada, imagenes_originales):
    nombre_base = nombre_imagen_recortada.split('_crop')[0]
    return imagenes_originales.get(nombre_base, None)

def crear_video(nombre, imagenes, directorio_videos):
    if not imagenes:
        return None
    os.makedirs(directorio_videos, exist_ok=True)
    imagenes.sort(key=lambda x: os.path.getmtime(x))
    frame = cv2.imread(imagenes[0])
    if frame is None:
        return None
    height, width, _ = frame.shape
    video_path = os.path.join(directorio_videos, f"{nombre}.mp4")
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 1, (width, height))
    for imagen in imagenes:
        frame = cv2.imread(imagen)
        if frame is not None:
            out.write(frame)
    out.release()
    return video_path

def resumen_gatos_en_24_horas(directorio_base, imagenes_originales):
    resumen, fotos, videos = {}, {}, {}
    for gato in os.listdir(directorio_base):
        path_gato = os.path.join(directorio_base, gato)
        if os.path.isdir(path_gato) and gato != "dudosos":
            resumen[gato], fotos[gato], videos[gato] = [], [], []
            for imagen in os.listdir(path_gato):
                path_imagen = os.path.join(path_gato, imagen)
                if os.path.isfile(path_imagen) and es_reciente(path_imagen):
                    camara = obtener_camara_de_imagen(imagen)
                    fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(path_imagen))
                    resumen[gato].append((fecha_modificacion, camara))
                    original = buscar_imagen_original(imagen, imagenes_originales)
                    fotos[gato].append(original if original else path_imagen)
                    videos[gato].append(original if original else path_imagen)
    for gato in resumen:
        resumen[gato].sort()
        fotos[gato] = [f for _, f in sorted(zip([d[0] for d in resumen[gato]], fotos[gato]))]
        videos[gato].sort(key=lambda x: os.path.getmtime(x))
    return resumen, fotos, videos

def crear_cuerpo_email_gatos(resumen, fotos):
    html = """<html><body><h1>Resumen de Gatos Detectados en las Últimas 24 Horas</h1>
    <h3>Accede a más detalles en la aplicación de Home Assistant:</h3>
    <a href='https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Ffrigate/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Ffrigate%2Fvideos'>Ir a la aplicación</a>"""
    for gato, detecciones in resumen.items():
        html += f"<h2>{gato}</h2><ul>"
        for fecha, cam in detecciones:
            html += f"<li>{cam} a las {fecha.strftime('%Y-%m-%d %H:%M:%S')}</li>"
        html += "</ul><h3>Fotos:</h3><div style='display:flex;flex-wrap:wrap;'>"
        for foto in fotos[gato][:5]:
            html += f'<div style="margin:5px;"><img src="cid:{os.path.basename(foto)}" style="max-width:200px;"/></div>'
        html += "</div>"
    html += "</body></html>"
    return html

def crear_video_ezviz(directorio_entrada, directorio_salida):
    imagenes = [os.path.join(directorio_entrada, f) for f in sorted(os.listdir(directorio_entrada)) if f.lower().endswith('.jpg')]
    return crear_video("ezviz_gatos", imagenes, directorio_salida)

def analizar_imagenes_openai(directorio_entrada, api_key):
    resultados = []
    client = OpenAI(api_key=api_key)
    for imagen_path in sorted(os.listdir(directorio_entrada)):
        if not imagen_path.lower().endswith(".jpg"):
            continue
        full_path = os.path.join(directorio_entrada, imagen_path)
        with open(full_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode('utf-8')
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un experto en identificar gatos, colores, otros animales o personas en imágenes."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Describe todos los animales visibles (gatos, zorros, personas, etc.) y sus colores."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]}
                ],
                max_tokens=500
            )
            descripcion = response.choices[0].message.content
            resultados.append(descripcion)
        except Exception as e:
            resultados.append(f"Error: {str(e)}")
    return resultados

def resumen_global_openai(resultados, video_url):
    texto_completo = " ".join(resultados).lower()
    gatos = texto_completo.count("gato")
    personas = texto_completo.count("persona")
    animales = texto_completo.count("perro") + texto_completo.count("zorro") + texto_completo.count("conejo")
    html = f"""<html><body>
    <h1>Resumen Global del Análisis Ezviz</h1>
    <ul>
        <li>Gatos detectados (menciones): {gatos}</li>
        <li>Personas detectadas (menciones): {personas}</li>
        <li>Otros animales (menciones): {animales}</li>
    </ul>
    <h3>Ver el vídeo generado:</h3>
    <a href="{video_url}">{video_url}</a>
    </body></html>"""
    return html

def send_email(subject, body, destinatarios, imagenes_embed=None):
    sender_email = "75642e001@smtp-brevo.com"
    password = "8nP5LXfVT1tmvCgW"
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(destinatarios)
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
    if imagenes_embed:
        for imagen_path in imagenes_embed:
            try:
                with open(imagen_path, "rb") as f:
                    img_data = f.read()
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', f"<{os.path.basename(imagen_path)}>")
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(imagen_path))
                    message.attach(img)
            except Exception as e:
                logging.error(f"Error adjuntando imagen {imagen_path}: {str(e)}")
    try:
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, destinatarios, message.as_string())
        server.close()
        logging.info("Email enviado correctamente")
    except Exception as e:
        logging.error(f"Error enviando email: {str(e)}")

if __name__ == "__main__":
    with open("/data/options.json") as f:
        options = json.load(f)
    api_key = options.get("openai_api_key")

    # EMAIL 1: RESUMEN GATOS
    directorio_base = "/media/frigate/clasificado"
    directorio_originales = "/media/frigate/originales"
    directorio_videos = "/media/frigate/videos"
    imagenes_originales = cargar_imagenes_originales(directorio_originales)
    resumen, fotos, videos = resumen_gatos_en_24_horas(directorio_base, imagenes_originales)
    for gato, imagenes in videos.items():
        crear_video(gato, imagenes, directorio_videos)
    cuerpo_email_gatos = crear_cuerpo_email_gatos(resumen, fotos)
    asunto_gatos = f"Resumen de Gatos - {datetime.now().strftime('%Y-%m-%d')}"
    destinatarios = ["julioalberto85@gmail.com", "nuriagiadas@gmail.com"]
    imagenes_email = sum([fotos[g][:5] for g in fotos], [])
    send_email(asunto_gatos, cuerpo_email_gatos, destinatarios, imagenes_email)

    # EMAIL 2: RESUMEN OPENAI + VIDEO EZVIZ
    directorio_ezviz = "/config/ezviz_gatitos"
    directorio_media_ezviz = "/media/ezviz_gatitos"
    video_path = crear_video_ezviz(directorio_ezviz, directorio_media_ezviz)
    resultados_openai = analizar_imagenes_openai(directorio_ezviz, api_key)
    video_url = "https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Fezviz_gatitos"
    cuerpo_email_ezviz = resumen_global_openai(resultados_openai, video_url)
    asunto_ezviz = f"Resumen Ezviz OpenAI - {datetime.now().strftime('%Y-%m-%d')}"
    send_email(asunto_ezviz, cuerpo_email_ezviz, destinatarios)
