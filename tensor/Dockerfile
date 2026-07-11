FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_CPP_MIN_LOG_LEVEL=2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install \
        tensorflow==2.20.0 \
        numpy==1.26.4 \
        pillow==10.4.0 \
        opencv-python-headless==4.10.0.84

COPY ./app /app

CMD ["python", "script.py"]
