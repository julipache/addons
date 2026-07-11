import subprocess
import time


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


if __name__ == "__main__":
    while True:
        # Frigate ya detecta los gatos. Este add-on solo clasifica los recortes
        # existentes en /media/frigate/recortadas.
        run_script("pruebamsiva.py")

        print("Waiting for 1 hour before the next run.", flush=True)
        time.sleep(3600)
