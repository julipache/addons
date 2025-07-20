from flask import Flask, render_template_string, request, jsonify, send_file
import shutil
import os
import json

app = Flask(__name__)

# 📂 Rutas
BASE_DIR = r"D:\identificaciongatos\solo_clean"
VALIDADAS_DIR = r"D:\identificaciongatos\validadas"
DUDOSOS_DIR = r"D:\identificaciongatos\dudosos"
PROGRESO_FILE = "progreso.json"

# 🐱 Lista fija de gatos
gatos = ["coco", "pina", "snape", "ray", "pollo", "sdg"]

# 📝 Estado del progreso
if os.path.exists(PROGRESO_FILE):
    with open(PROGRESO_FILE, "r") as f:
        progreso = json.load(f)
        carpeta_actual_idx = progreso.get("carpeta_actual_idx", 0)
        fotos_marcadas = progreso.get("fotos_marcadas", {})
else:
    carpeta_actual_idx = 0
    fotos_marcadas = {}

# 📸 Cargar fotos pendientes de la carpeta actual
def cargar_fotos():
    carpeta_actual = gatos[carpeta_actual_idx]
    carpeta_path = os.path.join(BASE_DIR, carpeta_actual)
    fotos = []
    for archivo in os.listdir(carpeta_path):
        path = os.path.join(carpeta_path, archivo)
        if path not in fotos_marcadas:
            fotos.append(path)
    return fotos

fotos_pendientes = cargar_fotos()

@app.route("/")
def index():
    carpeta_actual = gatos[carpeta_actual_idx] if carpeta_actual_idx < len(gatos) else "⚠️ Ninguna"
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Validador de fotos 🐱</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background: #f5f5f5; }
            img { max-width: 80%; max-height: 80vh; border: 5px solid #333; border-radius: 10px; margin: 20px 0; }
            .gato-btn, .carpeta-btn {
                display: inline-block;
                margin: 5px;
                padding: 10px 15px;
                font-size: 1.2em;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            .gato-btn:hover, .carpeta-btn:hover {
                background-color: #0056b3;
            }
            .dudoso-btn {
                display: inline-block;
                margin: 5px;
                padding: 10px 15px;
                font-size: 1.2em;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            .dudoso-btn:hover {
                background-color: #a71d2a;
            }
        </style>
    </head>
    <body>
        <h1>Validador de fotos 🐱</h1>
        <h3>📂 Carpeta actual: {{ carpeta_actual }}</h3>
        <div id="foto-container">
            <p>Cargando...</p>
        </div>
        <div id="gato-buttons">
            {% for gato in gatos %}
            <button class="gato-btn" onclick="asignarGato('{{ gato }}')">{{ loop.index }}️⃣ {{ gato }}</button>
            {% endfor %}
            <button class="dudoso-btn" onclick="marcarDudoso()">0️⃣ Dudoso</button>
        </div>
        <div style="margin-top: 20px;">
            <button class="carpeta-btn" onclick="siguienteGato()">➡️ Siguiente gato</button>
        </div>
        <script>
            let fotos = [];
            let actual = 0;
            let gatos = {{ gatos|tojson }};

            function cargarFotos() {
                fetch("/fotos").then(res => res.json()).then(data => {
                    fotos = data;
                    mostrarSiguiente();
                });
            }

            function mostrarSiguiente() {
                if (actual >= fotos.length) {
                    document.getElementById("foto-container").innerHTML = "<h2>✅ ¡No hay más fotos en esta carpeta!</h2>";
                    return;
                }
                const foto = fotos[actual];
                document.getElementById("foto-container").innerHTML = `
                    <img src="/imagen?path=${encodeURIComponent(foto)}">
                    <p>${foto}</p>
                `;
            }

            function asignarGato(gato) {
                const foto = fotos[actual];
                fetch("/asignar", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ path: foto, gato })
                }).then(() => {
                    actual++;
                    mostrarSiguiente();
                });
            }

            function marcarDudoso() {
                const foto = fotos[actual];
                fetch("/dudoso", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ path: foto })
                }).then(() => {
                    actual++;
                    mostrarSiguiente();
                });
            }

            function siguienteGato() {
                fetch("/siguiente_gato", { method: "POST" }).then(() => {
                    location.reload();
                });
            }

            document.addEventListener("keydown", function(event) {
                if (event.key === "0") {
                    marcarDudoso();
                } else {
                    let idx = parseInt(event.key) - 1;
                    if (!isNaN(idx) && idx >= 0 && idx < gatos.length) {
                        asignarGato(gatos[idx]);
                    }
                }
            });

            window.onload = cargarFotos;
        </script>
    </body>
    </html>
    """, gatos=gatos, carpeta_actual=carpeta_actual)

@app.route("/fotos")
def get_fotos():
    return jsonify(fotos_pendientes)

@app.route("/imagen")
def serve_imagen():
    path = request.args.get("path")
    if os.path.exists(path):
        return send_file(path)
    else:
        return "Not Found", 404

@app.route("/asignar", methods=["POST"])
def asignar():
    data = request.json
    path = data["path"]
    gato = data["gato"]
    destino = os.path.join(VALIDADAS_DIR, gato)
    os.makedirs(destino, exist_ok=True)
    shutil.move(path, os.path.join(destino, os.path.basename(path)))
    fotos_marcadas[path] = gato
    guardar_progreso()
    return jsonify({"status": "ok"})

@app.route("/dudoso", methods=["POST"])
def dudoso():
    data = request.json
    path = data["path"]
    os.makedirs(DUDOSOS_DIR, exist_ok=True)
    shutil.move(path, os.path.join(DUDOSOS_DIR, os.path.basename(path)))
    fotos_marcadas[path] = "dudoso"
    guardar_progreso()
    return jsonify({"status": "ok"})

@app.route("/siguiente_gato", methods=["POST"])
def siguiente_gato():
    global carpeta_actual_idx, fotos_pendientes
    if carpeta_actual_idx + 1 < len(gatos):
        carpeta_actual_idx += 1
        fotos_pendientes[:] = cargar_fotos()
        print(f"➡️ Cambiado a carpeta: {gatos[carpeta_actual_idx]}")
    guardar_progreso()
    return jsonify({"status": "ok"})

def guardar_progreso():
    with open(PROGRESO_FILE, "w") as f:
        json.dump({
            "carpeta_actual_idx": carpeta_actual_idx,
            "fotos_marcadas": fotos_marcadas
        }, f, indent=2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)