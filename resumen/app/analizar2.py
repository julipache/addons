import os
import time
import cv2
import smtplib
import json
import base64
import httpx
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

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

def crear_video_ezviz(directorio_entrada, directorio_salida):
    imagenes = [os.path.join(directorio_entrada, f) for f in sorted(os.listdir(directorio_entrada)) if f.lower().endswith('.jpg')]
    return crear_video("ezviz_gatos", imagenes, directorio_salida)

def analizar_imagenes_openai(directorio_entrada, api_key):
    resultados = []
    headers = {"Authorization": f"Bearer {api_key}"}
    for imagen_path in sorted(os.listdir(directorio_entrada)):
        if not imagen_path.lower().endswith(".jpg"):
            continue
        full_path = os.path.join(directorio_entrada, imagen_path)
        with open(full_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode('utf-8')
        prompt = [
            {"role": "system", "content": "Eres un experto en identificar gatos, colores, otros animales o personas en imágenes."},
            {"role": "user", "content": [
                {"type": "text", "text": "Describe todos los animales visibles (gatos, zorros, personas, etc.) y sus colores."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]}
        ]
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={"model": "gpt-4o", "messages": prompt, "max_tokens": 500},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                descripcion = data["choices"][0]["message"]["content"]
                resultados.append((imagen_path, descripcion))
            else:
                resultados.append((imagen_path, f"Error: {response.status_code} - {response.text}"))
        except Exception as e:
            resultados.append((imagen_path, f"Excepción: {str(e)}"))
    return resultados

def generar_email_ezviz(resultados):
    html = """<html><body><h1>Resumen de análisis de imágenes Ezviz</h1>"""
    for imagen, descripcion in resultados:
        html += f"<h3>{imagen}</h3><p>{descripcion}</p><hr>"
    html += """</body></html>"""
    return html

def send_email(subject, body, destinatarios):
    sender_email = "75642e001@smtp-brevo.com"
    password = "8nP5LXfVT1tmvCgW"
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(destinatarios)
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
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
    directorio_ezviz = "/config/ezviz_gatitos"
    directorio_media_ezviz = "/media/ezviz_gatitos"

    crear_video_ezviz(directorio_ezviz, directorio_media_ezviz)
    resultados = analizar_imagenes_openai(directorio_ezviz, api_key)
    cuerpo_email = generar_email_ezviz(resultados)
    asunto = f"Análisis de imágenes Ezviz - {datetime.now().strftime('%Y-%m-%d')}"
    destinatarios = ["julioalberto85@gmail.com", "nuriagiadas@gmail.com"]
    send_email(asunto, cuerpo_email, destinatarios)
    send_email(asunto, cuerpo_email, destinatarios)