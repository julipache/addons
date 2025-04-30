import os
import logging
import base64
from datetime import datetime, timedelta
from openai import OpenAI

# ... (otras importaciones y configuraciones sin cambio)

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


if __name__ == "__main__":
    logging.info("Generando resumen...")
    resumen, fotos, videos_gatos = resumen_gatos()
    if any(resumen.values()):
        cuerpo_email = crear_cuerpo_email(resumen, "(análisis solo para EZVIZ más abajo)", fotos)
        send_email("Resumen de actividad de gatos", cuerpo_email, fotos, destinatarios)

    logging.info("Creando video de EZVIZ...")
    video_ezviz_path = crear_video_ezviz()
    if video_ezviz_path:
        mover_video_a_media(video_ezviz_path)

        # Analizar solo imágenes de EZVIZ con OpenAI
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

        # Enviar email con resumen de EZVIZ
        link_video = "https://junucasa.duckdns.org:10/media-browser/browser/app%2Cmedia-source%3A%2F%2Fmedia_source/%2Cmedia-source%3A%2F%2Fmedia_source%2Flocal%2Fezviz_gatitos"
        send_email_video("Vídeo de movimiento EZVIZ", destinatarios, link_video, resumen_openai)


# Función modificada para incluir resumen_openai

def send_email_video(subject, destinatarios, link_video, resumen_openai):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = ", ".join(destinatarios)
    message['Subject'] = subject
    body = f"""
    <html><body>
    <h1>Vídeo de movimiento EZVIZ</h1>
    <p>Puedes ver el vídeo de las últimas 24 horas en el siguiente enlace:</p>
    <a href="{link_video}">Ver vídeo</a>
    <h2>Resumen visual generado por IA:</h2>
    <pre>{resumen_openai}</pre>
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