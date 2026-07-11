import logging
import os
import shutil

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("recortar_script.log"), logging.StreamHandler()],
)

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def detect_and_crop_cats(
    input_directory,
    output_directory,
    originals_directory,
    yolo_weights,
    yolo_cfg,
    yolo_names,
    conf_threshold=0.5,
    nms_threshold=0.4,
):
    net = cv2.dnn.readNet(yolo_weights, yolo_cfg)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    with open(yolo_names, "r", encoding="utf-8") as file:
        classes = [line.strip() for line in file.readlines()]

    logging.info("Classes loaded: %s", classes)
    processed = 0
    detected = 0

    for subdir, _, files in os.walk(input_directory):
        for filename in files:
            lower_name = filename.lower()
            if "-clean" not in lower_name or not lower_name.endswith(SUPPORTED_EXTENSIONS):
                continue

            processed += 1
            img_path = os.path.join(subdir, filename)
            logging.info("Processing image: %s", img_path)
            img = cv2.imread(img_path, cv2.IMREAD_COLOR)

            if img is None:
                logging.error("Error loading image %s", img_path)
                continue

            height, width, _ = img.shape
            blob = cv2.dnn.blobFromImage(
                img,
                0.00392,
                (416, 416),
                (0, 0, 0),
                True,
                crop=False,
            )
            net.setInput(blob)
            outs = net.forward(output_layers)

            boxes = []
            confidences = []
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = int(np.argmax(scores))
                    confidence = float(scores[class_id])
                    if confidence > conf_threshold and classes[class_id] == "cat":
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        boxes.append([x, y, w, h])
                        confidences.append(confidence)
                        logging.info(
                            "Detected cat with confidence %.2f at [%d, %d, %d, %d]",
                            confidence,
                            x,
                            y,
                            w,
                            h,
                        )

            relative_path = os.path.relpath(subdir, input_directory)
            originals_subdir = os.path.join(originals_directory, relative_path)
            os.makedirs(originals_subdir, exist_ok=True)
            original_destination = os.path.join(originals_subdir, filename)
            if os.path.exists(original_destination):
                base, ext = os.path.splitext(filename)
                original_destination = os.path.join(
                    originals_subdir, f"{base}_{processed}{ext}"
                )
            shutil.move(img_path, original_destination)
            logging.info("Moved original image to %s", original_destination)

            if not boxes:
                logging.info("No cats detected in %s", filename)
                continue

            indexes = cv2.dnn.NMSBoxes(
                boxes, confidences, conf_threshold, nms_threshold
            )
            selected_indexes = set(np.array(indexes).flatten().tolist()) if len(indexes) else set()

            for i, (x, y, w, h) in enumerate(boxes):
                if i not in selected_indexes:
                    continue

                x = max(0, x)
                y = max(0, y)
                w = min(w, width - x)
                h = min(h, height - y)
                crop_img = img[y : y + h, x : x + w]

                if crop_img.size == 0:
                    logging.info("Skipping empty crop for image %s", filename)
                    continue

                output_subdir = os.path.join(output_directory, relative_path)
                os.makedirs(output_subdir, exist_ok=True)

                base, _ = os.path.splitext(filename)
                suffix = f"_{i + 1}" if len(selected_indexes) > 1 else ""
                output_path = os.path.join(
                    output_subdir, f"{base}_crop{suffix}.jpg"
                )
                cv2.imwrite(
                    output_path,
                    crop_img,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 100],
                )
                detected += 1
                logging.info("Saved cropped image to %s", output_path)

    logging.info(
        "Crop run completed: %d clean images processed, %d cat crops generated",
        processed,
        detected,
    )


if __name__ == "__main__":
    detect_and_crop_cats(
        "/media/frigate/clips",
        "/media/frigate/recortadas",
        "/media/frigate/originales",
        "/media/yolov3.weights",
        "/media/yolov3.cfg",
        "/media/coco.names",
    )
