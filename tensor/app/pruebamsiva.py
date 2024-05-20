import numpy as np
import os
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

def load_and_prepare_image(img_path, target_size=(128, 128)):
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return img_array

def predict_directory_images(directory_path):
    model_path = 'mi_modelo_entrenado.h5'
    model = load_model(model_path)
    class_labels = {0: 'coco',1: 'pina', 2: 'pollo', 3: 'ray',4: 'snape'}  # Ajusta según tus clases
    
    correct_predictions = {}
    total_predictions = {}
    for label in class_labels.values():  # Initialize dictionaries
        correct_predictions[label] = 0
        total_predictions[label] = 0

    # List all files in directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".png") or filename.endswith(".jpg"):  # Check for image files
            img_path = os.path.join(directory_path, filename)
            img = load_and_prepare_image(img_path)
            predictions = model.predict(img)
            predicted_class_index = np.argmax(predictions, axis=1)
            predicted_class_name = class_labels[predicted_class_index[0]]
            confidence = np.max(predictions) * 100  # Confidence of the prediction
            actual_class_name = filename.split('_')[0]  # Assuming file name starts with the class name

            print(f"File: {filename} - Predicted: {predicted_class_name} ({confidence:.2f}%), Actual: {actual_class_name}")

            if actual_class_name in class_labels.values():  # Ensure actual name is one of the known classes
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

# Path to the directory containing images
directory_path = '/media/frigate/clips/sala_estar'
predict_directory_images(directory_path)
