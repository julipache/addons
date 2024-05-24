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

def load_and_prepare_image(img_path, target_size=(128, 128)):
    try:
        img = image.load_img(img_path, target_size=target_size)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return img_array
    except Exception as e:
        print(f"Error processing image {img_path}: {str(e)}")
        return None

def send_email(subject, body):
    sender_email = "75642e001@smtp-brevo.com"
    receiver_email = "julioalberto85@gmail.com"  # Reemplaza con el correo del destinatario
    password = "8nP5LXfVT1tmvCgW"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.close()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def predict_directory_images(directory_path, model_path, confidence_threshold=60.0):
    if not os.path.exists(directory_path):
        print(f"Directory does not exist: {directory_path}")
        return

    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}")
        return

    model = load_model(model_path)
    class_labels = {0: 'coco', 1: 'pina', 2: 'pollo', 3: 'ray', 4: 'snape'}  # Adjust as per your classes
    
    correct_predictions = {label: 0 for label in class_labels.values()}
    total_predictions = {label: 0 for label in class_labels.values()}
    
    # Directorio para imágenes dudosas
    doubtful_dir = os.path.join(directory_path, 'dudosos')
    os.makedirs(doubtful_dir, exist_ok=True)

    analysis_report = ""

    for filename in os.listdir(directory_path):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            img_path = os.path.join(directory_path, filename)
            img = load_and_prepare_image(img_path)
            if img is None:
                continue

            predictions = model.predict(img)
            predicted_class_index = np.argmax(predictions, axis=1)
            predicted_class_name = class_labels[predicted_class_index[0]]
            confidence = np.max(predictions) * 100

            if confidence < confidence_threshold:
                report_line = f"File: {filename} - Prediction confidence ({confidence:.2f}%) below threshold, moved to 'dudosos'."
                print(report_line)
                analysis_report += report_line + "\n"
                shutil.move(img_path, os.path.join(doubtful_dir, filename))
                continue

            actual_class_name = filename.split('_')[0]
            target_folder = os.path.join(directory_path, predicted_class_name)
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(img_path, os.path.join(target_folder, filename))

            report_line = f"File: {filename} - Predicted: {predicted_class_name} ({confidence:.2f}%), Actual: {actual_class_name}"
            print(report_line)
            analysis_report += report_line + "\n"

            if actual_class_name in class_labels.values():
                total_predictions[actual_class_name] += 1
                if predicted_class_name == actual_class_name:
                    correct_predictions[actual_class_name] += 1

    for class_name in class_labels.values():
        if total_predictions[class_name] > 0:
            accuracy = (correct_predictions[class_name] / total_predictions[class_name]) * 100
            report_line = f"Accuracy for {class_name}: {accuracy:.2f}% ({correct_predictions[class_name]}/{total_predictions[class_name]})"
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
