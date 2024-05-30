import os
import cv2
import numpy as np

def detect_and_crop_cats(input_directory, output_directory, yolo_weights, yolo_cfg, yolo_names, conf_threshold=0.5, nms_threshold=0.4):
    # Load YOLO
    net = cv2.dnn.readNet(yolo_weights, yolo_cfg)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    # Load class names
    with open(yolo_names, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    for subdir, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(".jpg") or file.endswith(".png"):
                img_path = os.path.join(subdir, file)
                img = cv2.imread(img_path)

                if img is None:
                    print(f"Error loading image {img_path}")
                    continue

                height, width, channels = img.shape
                blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                net.setInput(blob)
                outs = net.forward(output_layers)

                # Initialization
                class_ids = []
                confidences = []
                boxes = []

                # For each detection from each output layer
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        # Filter detections by confidence and class
                        if confidence > conf_threshold and classes[class_id] == 'cat':
                            # Object detected
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)
                            # Rectangle coordinates
                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)
                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)

                # Apply non-max suppression
                indexes = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]

                        # Ensure the coordinates are within the image bounds
                        x = max(0, x)
                        y = max(0, y)
                        w = min(w, width - x)
                        h = min(h, height - y)

                        # Crop the detected cat
                        crop_img = img[y:y+h, x:x+w]

                        # Ensure the cropped image is not empty
                        if crop_img.size == 0:
                            print(f"Skipping empty crop for image {img_path}")
                            continue

                        # Create the output subdirectory if it doesn't exist
                        relative_path = os.path.relpath(subdir, input_directory)
                        output_subdir = os.path.join(output_directory, relative_path)
                        if not os.path.exists(output_subdir):
                            os.makedirs(output_subdir)

                        # Save the cropped image
                        output_path = os.path.join(output_subdir, file)
                        cv2.imwrite(output_path, crop_img)
                        print(f"Saved cropped image to {output_path}")

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
