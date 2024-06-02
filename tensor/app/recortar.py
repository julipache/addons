import os
import cv2
import numpy as np
import logging
import shutil


# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("recortar_script.log"),
    logging.StreamHandler()
])

def detect_and_crop_cats(input_directory, output_directory, yolo_weights, yolo_cfg, yolo_names, conf_threshold=0.5, nms_threshold=0.4):
    net = cv2.dnn.readNet(yolo_weights, yolo_cfg)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    with open(yolo_names, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    logging.info(f"Classes loaded: {classes}")

    for subdir, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(".jpg") or file.endswith(".png"):
                img_path = os.path.join(subdir, file)
                logging.info(f"Processing image: {img_path}")
                img = cv2.imread(img_path)

                if img is None:
                    logging.error(f"Error loading image {img_path}")
                    continue

                height, width, channels = img.shape
                blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                net.setInput(blob)
                outs = net.forward(output_layers)

                boxes = []
                confidences = []
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > conf_threshold and classes[class_id] == 'cat':
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)
                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)
                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            logging.info(f"Detected cat with confidence {confidence:.2f} at [{x}, {y}, {w}, {h}]")

                if len(boxes) == 0:
                    # No cats detected, move image to 'nodetectados' folder
                    relative_path = os.path.relpath(subdir, input_directory)
                    output_subdir = os.path.join(output_directory, 'nodetectados', relative_path)
                    if not os.path.exists(output_subdir):
                        os.makedirs(output_subdir)
                    output_path = os.path.join(output_subdir, file)
                    shutil.move(img_path, output_path)
                    logging.info(f"Moved image with no detections to {output_path}")
                    continue

                indexes = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]
                        x = max(0, x)
                        y = max(0, y)
                        w = min(w, width - x)
                        h = min(h, height - y)
                        crop_img = img[y:y+h, x:x+w]

                        if crop_img.size == 0:
                            logging.info(f"Skipping empty crop for image {img_path}")
                            continue

                        relative_path = os.path.relpath(subdir, input_directory)
                        output_subdir = os.path.join(output_directory, relative_path)
                        if not os.path.exists(output_subdir):
                            os.makedirs(output_subdir)

                        base, ext = os.path.splitext(file)
                        output_path = os.path.join(output_subdir, f"{base}_crop{ext}")
                        cv2.imwrite(output_path, crop_img)
                        logging.info(f"Saved cropped image to {output_path}")

                        # Dibujar un cuadro alrededor del gato detectado y guardar la imagen
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        detection_output_path = os.path.join(output_subdir, f"{base}_detection{ext}")
                        cv2.imwrite(detection_output_path, img)
                        logging.info(f"Saved detection image to {detection_output_path}")

                # Eliminar la imagen original después de procesarla
                os.remove(img_path)
                logging.info(f"Deleted original image {img_path}")

if __name__ == "__main__":
    #input_directory = 'D:\\identificaciongatos\\recortads\\analizar'
    input_directory = '/media/frigate/clips/sala_estar'
    #output_directory = 'D:\\identificaciongatos\\recortads\\analizar_recortado'
    output_directory = '/media/frigate/clips/sala_estar_recortado'
    
    #model_path = '/media/mi_modelo_entrenado.keras'
    
    yolo_weights = '/media/yolov3.weights'  # Path to YOLO weights file

    yolo_cfg = '/media/yolov3.cfg'          # Path to YOLO config file
    yolo_names = '/media/coco.names'        # Path to file with class names
    detect_and_crop_cats(input_directory, output_directory, yolo_weights, yolo_cfg, yolo_names)