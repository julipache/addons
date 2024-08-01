import os
import logging
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import cv2
import time

# Configurar logging para consola y archivo
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

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
    for root, dirs, files in os.walk(directorio_originales):
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

    # Crear el directorio de salida si no existe
    os.makedirs(directorio_videos, exist_ok=True)

    # Ordenar las imágenes cronológicamente
    imagenes.sort(key=lambda x: os.path.getmtime(x))
    
    # Leer la primera imagen para obtener el tamaño del video
    frame = cv2.imread(imagenes[0])
    if frame is None:
        logging.error(f"Error al leer la imagen {imagenes[0]}")
        return None
    
    height, width, layers = frame.shape
    size = (width, height)
    
    # Inicializar el objeto de escritura de video
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
    """
    Genera un resumen de las cámaras y horarios por donde estuvo cada gato en las últimas 24 horas.
    """
    resumen = {}
    fotos = {}
    videos = {}

    start_time = time.time()
    for gato in os.listdir(directorio_base):
        path_gato = os.path.join(directorio_base, gato)
        if os.path.isdir(path_gato) and gato != "dudosos":
            resumen[gato] = []
            fotos[gato] = []
            videos[gato] = []
            for imagen in os.listdir(path_gato):
                path_imagen = os.path.join(path_gato, imagen)
                if os.path.isfile(path_imagen) and es_reciente(path_imagen):
                    camara = obtener_camara_de_imagen(imagen)
                    fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(path_imagen))
                    resumen[gato].append((fecha_modificacion, camara))
                    
                    # Buscar la imagen original
                    path_imagen_original = buscar_imagen_original(imagen, imagenes_originales)
                    if path_imagen_original:
                        fotos[gato].append(path_imagen_original)
                        videos[gato].append(path_imagen_original)
                    else:
                        fotos[gato].append(path_imagen)  # Usar la imagen recortada si no se encuentra la original
                        videos[gato].append(path_imagen)
    logging.debug(f"Generar resumen de gatos tomó {time.time() - start_time} segundos")
    
    # Ordenar las detecciones por tiempo para cada gato
    for gato in resumen:
        resumen[gato].sort()
        fotos[gato] = [foto for _, foto in sorted(zip([fecha for fecha, _ in resumen[gato]], fotos[gato]))]
        videos[gato].sort(key=lambda x: os.path.getmtime(x))

    return resumen, fotos, videos

def crear_cuerpo_email(resumen, fotos):
    """
    Genera el cuerpo del email con el resumen de las cámaras y horarios por donde estuvo cada gato,
    incluyendo algunas fotos incrustadas.
    """
    html = """<html>
    <body>
    <h1>Resumen de Gatos Detectados en las Últimas 24 Horas</h1>
    """
    
    for gato, detecciones in resumen.items():
        if detecciones:
            html += f"<h2>{gato}</h2>"
            html += "<ul>"
            for fecha_modificacion, camara in detecciones:
                html += f"<li>{camara} a las {fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S')}</li>"
            html += "</ul>"
            
            if fotos[gato]:
                html += "<h3>Fotos:</h3>"
                # Incluir todas las fotos por gato
                for foto in fotos[gato]:
                    html += f'<img src="cid:{os.path.basename(foto)}" style="max-width:200px; margin:10px;"/><br>'
        else:
            html += f"<h2>{gato} no estuvo en ninguna cámara en las últimas 24 horas.</h2>"
    
    html += """
    </body>
    </html>
    """
    
    return html

def send_email(subject, body, fotos):
    sender_email = "75642e001@smtp-brevo.com"
    receiver_email = "julioalberto85@gmail.com"
    password = "8nP5LXfVT1tmvCgW"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    for gato, paths in fotos.items():
        for file_path in paths:  # Adjuntar todas las fotos involucradas en el resumen
            try:
                with open(file_path, "rb") as attachment:
                    img_data = attachment.read()
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', f"<{os.path.basename(file_path)}>")
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(file_path))
                    message.attach(img)
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
    directorio_base = r'/media/frigate/clasificado'
    directorio_originales = r'/media/frigate/originales'
    directorio_videos = r'/media/frigate/videos'
    
    # Cargar imágenes originales
    logging.debug("Cargando imágenes originales...")
    imagenes_originales = cargar_imagenes_originales(directorio_originales)
    
    # Generar el resumen de gatos en las últimas 24 horas
    logging.debug("Generando resumen de gatos en las últimas 24 horas...")
    resumen, fotos, videos = resumen_gatos_en_24_horas(directorio_base, imagenes_originales)
    
    # Crear videos para cada gato con las imágenes de las últimas 24 horas
    logging.debug("Creando videos para cada gato...")
    video_paths = {}
    start_time_videos = time.time()
    for gato, imagenes in videos.items():
        video_path = crear_video(gato, imagenes, directorio_videos)
        if video_path:
            video_paths[gato] = video_path
    logging.debug(f"Crear videos tomó {time.time() - start_time_videos} segundos")
    
    cuerpo_email = crear_cuerpo_email(resumen, fotos)
    print(cuerpo_email)  # También puedes imprimirlo en la consola si lo deseas
    
    # Calcular el rango de tiempo para el asunto del email
    hora_fin = datetime.now()
    hora_inicio = hora_fin - timedelta(hours=24)
    asunto = f"Resumen de Gatos Detectados desde {hora_inicio.strftime('%Y-%m-%d %H:%M:%S')} hasta {hora_fin.strftime('%Y-%m-%d %H:%M:%S')}"

    # Enviar el resumen por correo electrónico
    logging.debug("Enviando el resumen por correo electrónico...")
    send_email(
        subject=asunto,
        body=cuerpo_email,
        fotos=fotos
    )
    logging.debug("Proceso completado")
