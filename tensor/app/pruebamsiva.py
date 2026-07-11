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
