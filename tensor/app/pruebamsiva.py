import numpy as np
import os
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

def predict_directory_images(directory_path, model_path):
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

    # List all files in directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".png") or filename.endswith(".jpg"):  # Check for image files
            img_path = os.path.join(directory_path, filename)
            img = load_and_prepare_image(img_path)
            if img is None:
                continue

            predictions = model.predict(img)
            predicted_class_index = np.argmax(predictions, axis=1)
            predicted_class_name = class_labels[predicted_class_index[0]]
            confidence = np.max(predictions) * 100  # Confidence of the prediction
            actual_class_name = filename.split('_')[0]  # Assuming file name starts with the class name

            print(f"File: {filename} - Predicted: {predicted_class_name} ({confidence:.2f}%), Actual: {actual_class_name}")

            if actual_class_name in class_labels.values():
                total_predictions[actual_class_name] += 1
                if predicted_class_name == actual_class_name:
                    correct_predictions[actual_class_name] += 1

    # Calculate and print accuracy for each class
    for class_name in class_labels.values():
        if total_predictions[class_name] > 0:
            accuracy = (correct_predictions[class_name] / total_predictions[class_name]) * 100
            print(f"Accuracy for {class_name}: {accuracy:.2f}% ({correct_predictions[class_name]}/{total_predictions[class_name]})")
        else:
            print(f"No images to analyze for class {class_name}.")

# Path to the directory containing images and model
directory_path = '/media/frigate/clips/sala_estar'
model_path = '/media/mi_modelo_entrenado.h5'  # Update this path as necessary
predict_directory_images(directory_path, model_path)
