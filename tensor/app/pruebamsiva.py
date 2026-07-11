import csv
import json
import logging
import os
import shutil
from pathlib import Path

import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

INPUT_DIRECTORY = Path("/media/frigate/recortadas")
OUTPUT_DIRECTORY = Path("/media/frigate/clasificado")
DOUBTFUL_DIRECTORY = OUTPUT_DIRECTORY / "dudosos"
LOG_FILE_PATH = Path("/media/frigate/predicciones_log.csv")
PUBLIC_JSON_DIRECTORY = Path("/config/www/clasificado")
MODEL_PATH = Path("/media/mi_modelo_entrenado.keras")
LABELS_PATH = Path("/media/labels.json")
CONFIDENCE_THRESHOLD = 85.0
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def ensure_directories() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    DOUBTFUL_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PUBLIC_JSON_DIRECTORY.mkdir(parents=True, exist_ok=True)
    INPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)


def load_labels() -> dict[int, str]:
    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró {LABELS_PATH}. Copia labels.json junto al modelo."
        )

    with LABELS_PATH.open("r", encoding="utf-8") as file:
        raw_labels = json.load(file)

    if isinstance(raw_labels, dict):
        labels = {int(index): str(name) for index, name in raw_labels.items()}
    elif isinstance(raw_labels, list):
        labels = {index: str(name) for index, name in enumerate(raw_labels)}
    else:
        raise ValueError("labels.json debe contener un objeto o una lista.")

    expected_indexes = list(range(len(labels)))
    if sorted(labels) != expected_indexes:
        raise ValueError(
            "Los índices de labels.json deben ser consecutivos y empezar en 0."
        )

    if len(set(labels.values())) != len(labels):
        raise ValueError("labels.json contiene nombres de gato duplicados.")

    logging.info("Etiquetas cargadas: %s", labels)
    return labels


def load_classifier():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo en {MODEL_PATH}."
        )

    model = load_model(MODEL_PATH)
    logging.info("Modelo cargado desde %s", MODEL_PATH)
    return model


def validate_model_output(model, labels: dict[int, str]) -> None:
    output_shape = model.output_shape
    output_classes = output_shape[-1] if isinstance(output_shape, tuple) else None

    if output_classes is not None and int(output_classes) != len(labels):
        raise ValueError(
            "El modelo devuelve "
            f"{output_classes} clases, pero labels.json contiene {len(labels)}."
        )


def load_and_prepare_image(img_path: Path, target_size=(224, 224)) -> np.ndarray:
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    return np.expand_dims(img_array, axis=0)


def choose_target_folder(predicted_name: str, confidence: float) -> Path:
    if confidence < CONFIDENCE_THRESHOLD:
        return DOUBTFUL_DIRECTORY
    return OUTPUT_DIRECTORY / predicted_name


def unique_destination(target_folder: Path, filename: str) -> Path:
    destination = target_folder / filename
    if not destination.exists():
        return destination

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = target_folder / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def predict_and_classify_image(
    model,
    labels: dict[int, str],
    img_path: Path,
    log_writer,
) -> None:
    try:
        img_array = load_and_prepare_image(img_path)
        predictions = model.predict(img_array, verbose=0)

        if predictions.ndim != 2 or predictions.shape[0] != 1:
            raise ValueError(
                f"Salida inesperada del modelo para {img_path}: {predictions.shape}"
            )

        predicted_index = int(np.argmax(predictions[0]))
        if predicted_index not in labels:
            raise ValueError(
                f"El modelo devolvió el índice {predicted_index}, no definido en labels.json."
            )

        predicted_name = labels[predicted_index]
        confidence = float(np.max(predictions[0]) * 100)
        target_folder = choose_target_folder(predicted_name, confidence)
        target_folder.mkdir(parents=True, exist_ok=True)
        destination = unique_destination(target_folder, img_path.name)

        shutil.move(str(img_path), str(destination))
        log_writer.writerow(
            [img_path.name, predicted_name, f"{confidence:.4f}", str(destination)]
        )

        logging.info(
            "Procesada %s - Predicción: %s - Confianza: %.2f%% - Destino: %s",
            img_path,
            predicted_name,
            confidence,
            destination,
        )
    except Exception:
        logging.exception("Error procesando %s", img_path)


def update_public_json(labels: dict[int, str]) -> None:
    logging.info("Actualizando índices JSON públicos...")

    for class_name in [*labels.values(), "dudosos"]:
        source_folder = OUTPUT_DIRECTORY / class_name
        target_folder = PUBLIC_JSON_DIRECTORY / class_name
        target_folder.mkdir(parents=True, exist_ok=True)
        index_file = target_folder / "index.json"

        files = []
        if source_folder.exists():
            files = sorted(
                [
                    path.name
                    for path in source_folder.iterdir()
                    if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
                ],
                reverse=True,
            )

        with index_file.open("w", encoding="utf-8") as file:
            json.dump(files, file, ensure_ascii=False, indent=2)


def open_prediction_log():
    file_exists = LOG_FILE_PATH.exists() and LOG_FILE_PATH.stat().st_size > 0
    log_file = LOG_FILE_PATH.open("a", newline="", encoding="utf-8")
    writer = csv.writer(log_file)

    if not file_exists:
        writer.writerow(["Image", "Predicted Class", "Confidence", "Destination"])

    return log_file, writer


def main() -> None:
    ensure_directories()
    labels = load_labels()
    model = load_classifier()
    validate_model_output(model, labels)

    log_file, log_writer = open_prediction_log()
    try:
        for root, _, files in os.walk(INPUT_DIRECTORY):
            for filename in sorted(files):
                img_path = Path(root) / filename
                if img_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    predict_and_classify_image(
                        model,
                        labels,
                        img_path,
                        log_writer,
                    )
                    log_file.flush()
    finally:
        log_file.close()

    update_public_json(labels)
    logging.info("Clasificación de imágenes completada")


if __name__ == "__main__":
    main()
