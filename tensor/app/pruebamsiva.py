import numpy as np
import os
import shutil
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input
from datetime import datetime
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("script_execution.log"),
    logging.StreamHandler()
])

# Variables globales para mantener el registro de las capturas y el resumen
daily_attachments = []
summary_file_path = "daily_summary.txt"



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

def load_and_prepare_image(img_path, target_size=(224, 224)):
    try:
        img = image.load_img(img_path, target_size=target_size)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        img_array = img_array / 255.0
        return img_array
    except Exception as e:
        logging.error(f"Error processing image {img_path}: {str(e)}")
        return None



def update_summary(report_line):
    with open(summary_file_path, "a") as f:
        f.write(report_line + "\n")

def read_summary():
    if os.path.exists(summary_file_path):
        with open(summary_file_path, "r") as f:
            return f.read()
    return ""

def clear_summary():
    if os.path.exists(summary_file_path):
        os.remove(summary_file_path)

def predict_directory_images(directory_path, model_path, confidence_threshold=65.0):
    global daily_attachments

    if not os.path.exists(directory_path):
        logging.error(f"Directory does not exist: {directory_path}")
        return

    if not os.path.exists(model_path):
        logging.error(f"Model file not found at {model_path}")
        return

    model = load_model(model_path)
    logging.info("Model loaded successfully")
    class_labels = {0: 'coco', 1: 'pina', 2: 'pollo', 3: 'ray', 4: 'snape'}  # Ajustar según tus clases
    
    correct_predictions = {label: 0 for label in class_labels.values()}
    total_predictions = {label: 0 for label in class_labels.values()}
    
    doubtful_dir = os.path.join(directory_path, 'dudosos')
    os.makedirs(doubtful_dir, exist_ok=True)

    current_date = datetime.now().strftime("%Y-%m-%d")

    for filename in os.listdir(directory_path):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            img_path = os.path.join(directory_path, filename)
            img = load_and_prepare_image(img_path, target_size=(224, 224))
            if img is None:
                continue

            predictions = model.predict(img)
            predicted_class_index = np.argmax(predictions, axis=1)
            predicted_class_name = class_labels[predicted_class_index[0]]
            confidence = np.max(predictions) * 100

            logging.info(f"Processed {filename} - Predicted: {predicted_class_name}, Confidence: {confidence:.2f}%")

            if confidence < confidence_threshold:
                report_line = f"File: {filename} - Prediction confidence ({confidence:.2f}%) below threshold, moved to 'dudosos'."
                logging.info(report_line)
                update_summary(report_line)
                shutil.move(img_path, os.path.join(doubtful_dir, filename))
                daily_attachments.append(os.path.join(doubtful_dir, filename))
                continue

            actual_class_name = filename.split('_')[0]
            target_folder = os.path.join(directory_path, predicted_class_name, current_date)
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(img_path, os.path.join(target_folder, filename))
            daily_attachments.append(os.path.join(target_folder, filename))

            report_line = f"File: {filename} - Predicted: {predicted_class_name} ({confidence:.2f}%), Actual: {actual_class_name}"
            logging.info(report_line)
            update_summary(report_line)

            if actual_class_name in class_labels.values():
                total_predictions[actual_class_name] += 1
                if predicted_class_name == actual_class_name:
                    correct_predictions[actual_class_name] += 1

    summary = "Summary of detections:\n"
    for class_name in class_labels.values():
        if total_predictions[class_name] > 0:
            accuracy = (correct_predictions[class_name] / total_predictions[class_name]) * 100
            summary += f"{class_name}: {total_predictions[class_name]} times detected with accuracy {accuracy:.2f}%\n"
        else:
            summary += f"{class_name}: Not detected\n"
    logging.info(summary)
    update_summary(summary)

def load_configuration():
    try:
        with open('/data/options.json', 'r') as file:
            data = json.load(file)
            return data['interval']
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        return 3600  # Default to 1 hour if any error

def send_analysis_email():
    analysis_report = read_summary()
    if analysis_report.strip() or daily_attachments:
        send_email("Photo Analysis Report", analysis_report, daily_attachments)
    clear_summary()
    daily_attachments.clear()

def main():
    interval = load_configuration()  # Load the execution interval from configuration
    directory_path = '/media/frigate/clips/sala_estar_recortado'
    model_path = '/media/mi_modelo_entrenado.keras'
    
    
    logging.info("Starting prediction cycle")
    predict_directory_images(directory_path, model_path)
    logging.info("Prediction cycle completed")

    logging.info("Starting email sending cycle")
    #send_analysis_email()
    logging.info("Email sending cycle completed")
    
        
    sent_directory = '/media/frigate/clips/sala_estar_recortado_enviado'

    if not os.path.exists(sent_directory):
        os.makedirs(sent_directory)

    # Procesar y enviar imágenes
    process_and_send_images(directory_path, sent_directory)

        

if __name__ == "__main__":
    main()
