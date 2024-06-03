import os
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

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
    print(f"Preparing email with subject: {subject}")

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
            print(f"Attached file: {file_path}")
        except Exception as e:
            print(f"Error attaching file {file_path}: {str(e)}")

    try:
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.close()
        print("Email sent successfully")
    except smtplib.SMTPException as e:
        print(f"SMTP error sending email: {str(e)}")
    except Exception as e:
        print(f"General error sending email: {str(e)}")

# Enviar imágenes nuevas por email y moverlas a la carpeta "enviadas"
def process_and_send_images(directory_path, sent_directory):
    new_images = []
    print(f"Checking directory: {directory_path} for new images...")
    
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(".png") or filename.endswith(".jpg"):
                new_images.append(os.path.join(root, filename))

    if new_images:
        print(f"Found {len(new_images)} new images. Preparing to send...")
        send_email("New Image Analysis Report", "See attached images.", new_images)
        for img_path in new_images:
            rel_path = os.path.relpath(img_path, directory_path)
            sent_img_path = os.path.join(sent_directory, rel_path)
            os.makedirs(os.path.dirname(sent_img_path), exist_ok=True)
            shutil.move(img_path, sent_img_path)
            print(f"Moved {img_path} to {sent_img_path}")
    else:
        print("No new images found to send.")

if __name__ == "__main__":
    directory_path = '/media/frigate/clips/sala_estar_recortado'
    sent_directory = '/media/frigate/clips/sala_estar_recortado_enviado'
    
    if not os.path.exists(sent_directory):
        os.makedirs(sent_directory)
    
    # Probar envío de correo simple
    try:
        send_email("Test Email", "This is a test email without attachments.", [])
    except Exception as e:
        print(f"Error during test email: {str(e)}")
    
    # Procesar y enviar imágenes
    process_and_send_images(directory_path, sent_directory)
