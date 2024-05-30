# main.py

import subprocess
import time

def run_script(script_name, args=[]):
    result = subprocess.run(['python', script_name] + args, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print(f"Error running {script_name}: {result.stderr}")

if __name__ == "__main__":
    while True:
        # Ejecutar el script de detección y recorte de gatos
        run_script('recortar.py')

        # Ejecutar el script de identificación de gatos
        run_script('pruebamsiva.py')

        # Esperar un tiempo antes de la próxima ejecución (ejemplo: cada hora)
        time.sleep(3600)  # 3600 segundos = 1 hora
