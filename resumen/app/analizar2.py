import os
import time
import cv2
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

logging.basicConfig(level=logging.DEBUG)

def es_reciente(file_path, horas=24):
    """
    Verifica si el archivo fue modificado en las últimas 'horas' horas.
    """
    tiempo_limite = datetime.now() - timedelta(hours=horas)
    fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(file_path))
    return fecha_modificacion > tiempo_limite

def obtener_camara_de_imagen(nombre_imagen):
    """
    Extrae el nombre de la cámara del nombre de la imagen.
    """
    return nombre_imagen.split('-')[0]

def cargar_imagenes_originales(directorio_originales):
    """
    Carga todas las rutas de imágenes originales en un diccionario para acceso rápido.
    """
    imagenes_originales = {}
    start_time = time.time()
    for root, _, files in os.walk(directorio_originales):
        for file in files:
            if "-clean" in file:
                nombre_base = file.split('-clean')[0]
                imagenes_originales[nombre_base] = os.path.join(root, file)
    logging.debug(f"Cargar imágenes originales tomó {time.time() - start_time} segundos")
    return imagenes_originales

def buscar_imagen_original(nombre_imagen_recortada, imagenes_originales):
    """
    Busca la imagen original en el diccionario de imágenes originales.
    """
    nombre_base = nombre_imagen_recortada.split('_crop')[0]
    return imagenes_originales.get(nombre_base, None)

def crear_video(gato, imagenes, directorio_videos):
    """
    Crea un video para cada gato utilizando las imágenes en orden cronológico.
    """
    if not imagenes:
        return None

    os.makedirs(directorio_videos, exist_ok=True)
    imagenes.sort(key=lambda x: os.path.getmtime(x))
    frame = cv2.imread(imagenes[0])
    if frame is None:
        logging.error(f"Error al leer la imagen {imagenes[0]}")
        return None

    height, width, _ = frame.shape
    size = (width, height)
    video_path = os.path.join(directorio_videos, f"{gato}.mp4")
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 1, size)

    for imagen in imagenes:
        frame = cv2.imread(imagen)
        if frame is not None:
            out.write(frame)
        else:
            logging.error(f"Error al leer la imagen {imagen}")

    out.release()
    logging.info(f"Video de {gato} guardado en {video_path}")
    return video_path

def resumen_gatos_en_24_horas(directorio_base, imagenes_originales):
    resumen, fotos, videos = {}, {}, {}
    start_time = time.time()

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
                    path_imagen_original = buscar_imagen_original(imagen, imagenes_originales)
                    imagen_final = path_imagen_original if path_imagen_original else path_imagen
                    fotos[gato].append(imagen_final)
                    videos[gato].append(imagen_final)

    logging.debug(f"Generar resumen de gatos tomó {time.time() - start_time} segundos")

    for gato in resumen:
        resumen[gato].sort()
        fotos[gato] = [foto for _, foto in sorted(zip([f for f, _ in resumen[gato]], fotos[gato]))]
        videos[gato].sort(key=lambda x: os.path.getmtime(x))

    return resumen, fotos, videos

def crear_cuerpo_email(resumen, fotos):
    html = """<html><body><h1>Resumen de Gatos Detectados en las Últimas 24 Horas</h1>"""
    html += """
    <h3>Accede a más detalles en la aplicación de Home Assistant:</h3>
    <a href="https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Ffrigate/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Ffrigate%2Fvideos">Ir a la aplicación</a>
    """

    for gato, detecciones in resumen.items():
        if detecciones:
            html += f"<h2>{gato}</h2><ul>"
            for fecha, camara in detecciones:
                html += f"<li>{camara} a las {fecha.strftime('%Y-%m-%d %H:%M:%S')}</li>"
            html += "</ul><h3>Fotos:</h3>"
            for foto in fotos[gato][:5]:
                html += f'<img src="cid:{os.path.basename(foto)}" style="max-width:200px; margin:10px;"/><br>'
        else:
            html += f"<h2>{gato} no estuvo en ninguna cámara en las últimas 24 horas.</h2>"

    html += """
    <h3>Accede a más detalles en la aplicación de Home Assistant:</h3>
    <a href="https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Ffrigate/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Ffrigate%2Fvideos">Ir a la aplicación</a>
    </body></html>
    """
    return html

def send_email(subject, body, fotos, destinatarios):
    import json
    with open("/data/options.json") as f:
        options = json.load(f)
    password = options.get("emailpass")
    sender_email = "75642e001@smtp-brevo.com"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(destinatarios)
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    for paths in fotos.values():
        for file_path in paths[:5]:
            try:
                with open(file_path, "rb") as attachment:
                    img = MIMEImage(attachment.read())
                    img.add_header('Content-ID', f"<{os.path.basename(file_path)}>")
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(file_path))
                    message.attach(img)
            except Exception as e:
                logging.error(f"Error adjuntando imagen {file_path}: {str(e)}")

    try:
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, destinatarios, message.as_string())
        server.quit()
        logging.info("Email enviado correctamente")
    except Exception as e:
        logging.error(f"Error enviando email: {str(e)}")

if __name__ == "__main__":
    while True:
        directorio_base = "/media/frigate/clasificado"
        directorio_originales = "/media/frigate/originales"
        directorio_videos = "/media/frigate/videos"

        logging.debug("Cargando imágenes originales...")
        imagenes_originales = cargar_imagenes_originales(directorio_originales)

        logging.debug("Generando resumen de gatos en las últimas 24 horas...")
        resumen, fotos, videos = resumen_gatos_en_24_horas(directorio_base, imagenes_originales)

        logging.debug("Creando videos para cada gato...")
        for gato, imagenes in videos.items():
            crear_video(gato, imagenes, directorio_videos)

        cuerpo_email = crear_cuerpo_email(resumen, fotos)
        hora_fin = datetime.now()
        hora_inicio = hora_fin - timedelta(hours=24)
        asunto = f"Resumen de Gatos Detectados desde {hora_inicio.strftime('%Y-%m-%d %H:%M:%S')} hasta {hora_fin.strftime('%Y-%m-%d %H:%M:%S')}"
        destinatarios = ["julioalberto85@gmail.com", "nuriagiadas@gmail.com"]

        logging.debug("Enviando email...")
        send_email(asunto, cuerpo_email, fotos, destinatarios)
        logging.debug("Proceso completado")

        now = datetime.now()
        next_run = now.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1)
        time.sleep((next_run - now).total_seconds())
