import subprocess
import time
from pathlib import Path

YOLO_FILES = [
    Path("/media/yolov3.weights"),
    Path("/media/yolov3.cfg"),
    Path("/media/coco.names"),
]


def run_script(script_name, args=None):
    args = args or []
    print(f"Running script: {script_name} with arguments: {args}", flush=True)
    result = subprocess.run(
        ["python", script_name, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.stdout:
        print(result.stdout, flush=True)

    if result.returncode != 0:
        print(
            f"Error running {script_name} (exit {result.returncode}):\n{result.stderr}",
            flush=True,
        )
    elif result.stderr:
        print(result.stderr, flush=True)

    return result.returncode


def yolo_available():
    missing = [str(path) for path in YOLO_FILES if not path.exists()]
    if missing:
        print(
            "Cannot run recortar.py because these YOLO files are missing: "
            + ", ".join(missing),
            flush=True,
        )
        return False
    return True


if __name__ == "__main__":
    while True:
        if yolo_available():
            run_script("recortar.py")

        run_script("pruebamsiva.py")

        print("Waiting for 1 hour before the next run.", flush=True)
        time.sleep(3600)
