import os
import cv2
import numpy as np
import shutil
import json
import time
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Funciones para cargar y preparar imágenes para el modelo de clasificación
def load_and_prepare_image(img_array, target_size=(128, 128)):
    try:
        img = cv2.resize(img_array, target_size)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return img_array
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

# Funciones para cargar y usar el modelo YOLO
def load_yolo_model(config_path, weights_path, classes_path):
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    
    with open(classes_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
        
    return net, output_layers, classes

def detect_objects_yolo(img, net, output_layers, confidence_threshold=0.5, nms_threshold=0.4):
    height, width, channels = img.shape

    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > confidence_threshold:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)

    results = []
    if len(indices) > 0:
        for i in indices.flatten():
            box = boxes[i]
            results.append({
                'class_id': class_ids[i],
                'confidence': confidences[i],
                'box': box
            })

    return results

def predict_directory_images(directory_path, yolo_model, output_layers, yolo_classes, classification_model, class_labels, confidence_threshold=0.5):
    if not os.path.exists(directory_path):
        print(f"Directory does not exist: {directory_path}")
        return

    correct_predictions = {label: 0 for label in class_labels.values()}
    total_predictions = {label: 0 for label in class_labels.values()}

    for filename in os.listdir(directory_path):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            img_path = os.path.join(directory_path, filename)
            img = cv2.imread(img_path)
            detections = detect_objects_yolo(img, yolo_model, output_layers, confidence_threshold)

            for detection in detections:
                if yolo_classes[detection['class_id']] == 'cat':
                    x, y, w, h = detection['box']
                    cropped_img = img[y:y+h, x:x+w]

                    prepared_img = load_and_prepare_image(cropped_img)
                    if prepared_img is None:
                        continue

                    predictions = classification_model.predict(prepared_img)
                    predicted_class_index = np.argmax(predictions, axis=1)
                    predicted_class_name = class_labels[predicted_class_index[0]]
                    confidence = np.max(predictions) * 100

                    if confidence < confidence_threshold:
                        print(f"File: {filename} - Prediction confidence ({confidence:.2f}%) below threshold, no prediction made.")
                        continue

                    actual_class_name = filename.split('_')[0]
                    target_folder = os.path.join(directory_path, predicted_class_name)
                    os.makedirs(target_folder, exist_ok=True)
                    shutil.move(img_path, os.path.join(target_folder, filename))

                    print(f"File: {filename} - Predicted: {predicted_class_name} ({confidence:.2f}%), Actual: {actual_class_name}")

                    if actual_class_name in class_labels.values():
                        total_predictions[actual_class_name] += 1
                        if predicted_class_name == actual_class_name:
                            correct_predictions[actual_class_name] += 1

    for class_name in class_labels.values():
        if total_predictions[class_name] > 0:
            accuracy = (correct_predictions[class_name] / total_predictions[class_name]) * 100
            print(f"Accuracy for {class_name}: {accuracy:.2f}% ({correct_predictions[class_name]}/{total_predictions[class_name]})")

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
    config_path = '/media/yolov3.cfg'
    weights_path = '/media/yolov3.weights'
    classes_path = '/media/yolov3.txt'

    yolo_model, output_layers, yolo_classes = load_yolo_model(config_path, weights_path, classes_path)

    classification_model_path = '/media/mi_modelo_entrenado.h5'
    classification_model = load_model(classification_model_path)
    class_labels = {0: 'coco', 1: 'pina', 2: 'pollo', 3: 'ray', 4: 'snape'}  # Adjust as per your classes

    while True:
        predict_directory_images(directory_path, yolo_model, output_layers, yolo_classes, classification_model, class_labels)
        time.sleep(interval)

if __name__ == "__main__":
    main()
