import numpy as np
import os
import shutil
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        print(f"Error processing image {img_path}: {str(e)}")
        return None

def send_email(subject, body):
    sender_email = "75642e001@smtp-brevo.com"
    receiver_email = "julioalberto85@gmail.com"  # Reemplaza con el correo del destinatario
    password = "8nP5LXfVT1tmvCgW"

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
    os.makedirs(doubtful_dir, exist_ok=True)

    analysis_report = ""

    for filename in os.listdir(directory_path):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            report_line = f"File: {filename} - Predicted: {predicted_class_name} ({confidence:.2f}%), Actual: {actual_class_name}"
            print(report_line)
            analysis_report += report_line + "\n"

            if actual_class_name in class_labels.values():
                total_predictions[actual_class_name] += 1
            print(report_line)
            analysis_report += report_line + "\n"

    send_email("Photo Analysis Report", analysis_report)

def load_configuration():
    try:
        with open('/data/options.json', 'r') as file:
            data = json.load(file)
            return data['interval']
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        return 3600  # Default to 1 hour if any error

def main():
    interval = load_configuration()  # Load the execution interval from configuration
    directory_path = '/media/frigate/clips/sala_estar'
    model_path = '/media/mi_modelo_entrenado.h5'

    while True:
        predict_directory_images(directory_path, model_path)
        time.sleep(interval)

if __name__ == "__main__":
    main()
