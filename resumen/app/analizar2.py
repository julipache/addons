import os
import logging
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def es_reciente(file_path, horas=24):
    """
    Verifica si el archivo fue modificado en las últimas 'horas' horas.
    
    Args:
        file_path (str): La ruta del archivo.
        horas (int): Número de horas para verificar.
        
    Returns:
        bool: True si el archivo fue modificado en las últimas 'horas' horas, de lo contrario False.
    """
    tiempo_limite = datetime.now() - timedelta(hours=horas)
    fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(file_path))
    return fecha_modificacion > tiempo_limite

def obtener_camara_de_imagen(nombre_imagen):
    """
    Extrae el nombre de la cámara del nombre de la imagen.
    
    Args:
        nombre_imagen (str): Nombre del archivo de la imagen.
        
    Returns:
        str: Nombre de la cámara.
    """
    return nombre_imagen.split('-')[0]

def buscar_imagen_original(nombre_imagen_recortada, directorio_originales):
    """
    Busca la imagen original en el directorio de originales.
    
    Args:
        nombre_imagen_recortada (str): Nombre de la imagen recortada.
        directorio_originales (str): Directorio base donde se encuentran las imágenes originales.
        
    Returns:
        str: Ruta de la imagen original si se encuentra, de lo contrario None.
    """
    camara = obtener_camara_de_imagen(nombre_imagen_recortada)
    nombre_base = nombre_imagen_recortada.split('_crop')[0]
    
    for root, dirs, files in os.walk(os.path.join(directorio_originales, camara)):
        for file in files:
            if file.startswith(nombre_base) and "-clean" in file:
                return os.path.join(root, file)
    return None

def resumen_gatos_en_24_horas(directorio_base, directorio_originales):
    """
    Genera un resumen de las cámaras y horarios por donde estuvo cada gato en las últimas 24 horas.
    
    Args:
        directorio_base (str): Ruta base donde se encuentran las carpetas de los gatos.
        directorio_originales (str): Ruta base donde se encuentran las imágenes originales.
    """
    resumen = {}
    fotos = {}

    for gato in os.listdir(directorio_base):
        path_gato = os.path.join(directorio_base, gato)
        if os.path.isdir(path_gato) and gato != "dudosos":
            resumen[gato] = []
            fotos[gato] = []
            for imagen in os.listdir(path_gato):
                path_imagen = os.path.join(path_gato, imagen)
                if os.path.isfile(path_imagen) and es_reciente(path_imagen):
                    camara = obtener_camara_de_imagen(imagen)
                    fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(path_imagen))
                    resumen[gato].append((fecha_modificacion, camara))
                    
                    # Buscar la imagen original
                    path_imagen_original = buscar_imagen_original(imagen, directorio_originales)
                    if path_imagen_original:
                        fotos[gato].append(path_imagen_original)
                    else:
                        fotos[gato].append(path_imagen)  # Usar la imagen recortada si no se encuentra la original
    
    # Ordenar las detecciones por tiempo para cada gato
    for gato in resumen:
        resumen[gato].sort()

    return resumen, fotos

def crear_cuerpo_email(resumen, fotos):
    """
    Genera el cuerpo del email con el resumen de las cámaras y horarios por donde estuvo cada gato,
    incluyendo algunas fotos incrustadas.
    
    Args:
        resumen (dict): Diccionario con el resumen de cámaras y horarios por gato.
        fotos (dict): Diccionario con las rutas de fotos por gato.
        
    Returns:
        str: El cuerpo del email formateado como HTML.
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
                # Incluir entre 5 y 10 fotos por gato, de diferentes cámaras si es posible
                fotos_incluidas = set()
                fotos_mostradas = 0
                for foto in fotos[gato]:
                    camara = obtener_camara_de_imagen(os.path.basename(foto))
                    if fotos_mostradas < 10 and camara not in fotos_incluidas:
                        fotos_incluidas.add(camara)
                        html += f'<img src="cid:{os.path.basename(foto)}" style="max-width:200px; margin:10px;"/><br>'
                        fotos_mostradas += 1
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
        for file_path in paths[:10]:  # Adjuntar hasta 10 fotos por gato
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
    directorio_base = r'\\192.168.1.127\media\frigate\clasificado'
    directorio_originales = r'\\192.168.1.127\media\frigate\originales'
    resumen, fotos = resumen_gatos_en_24_horas(directorio_base, directorio_originales)
    cuerpo_email = crear_cuerpo_email(resumen, fotos)
    print(cuerpo_email)  # También puedes imprimirlo en la consola si lo deseas
    
    # Calcular el rango de tiempo para el asunto del email
    hora_fin = datetime.now()
    hora_inicio = hora_fin - timedelta(hours=24)
    asunto = f"Resumen de Gatos Detectados desde {hora_inicio.strftime('%Y-%m-%d %H:%M:%S')} hasta {hora_fin.strftime('%Y-%m-%d %H:%M:%S')}"

    # Enviar el resumen por correo electrónico
    send_email(
        subject=asunto,
        body=cuerpo_email,
        fotos=fotos
    )
