from flask import Flask, jsonify, send_from_directory, render_template_string, request, abort
import os
from datetime import datetime

app = Flask(__name__)

CLASIFICADO_DIR = "/media/frigate/clasificado"

@app.before_request
def adjust_ingress_path():
    ingress = request.headers.get("X-Ingress-Path")
    if ingress:
        app.url_map.script_name = ingress

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Panel de gatos 🐾</title>
      <style>
        body { font-family: sans-serif; margin: 1em; background: #f0f0f0; }
        .gato-card {
          background: white;
          margin: 1em 0;
          padding: 1em;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .fotos {
          display: flex;
          flex-wrap: wrap;
          gap: 15px;
          margin-top: 10px;
        }
        .foto-bloque {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 120px;
        }
        .foto-bloque img {
          width: 100px;
          height: 100px;
          object-fit: cover;
          border-radius: 6px;
        }
        .camara {
          font-weight: bold;
          font-size: 0.95em;
          margin-top: 5px;
        }
        .hora {
          font-size: 0.8em;
          color: #555;
        }
      </style>
    </head>
    <body>
      <h1>Panel de gatos 🐾</h1>
      <div id="panel">Cargando...</div>

      <script>
        const basePath = window.location.pathname.replace(/\\/$/, '');

        async function cargarGatos() {
          const panel = document.getElementById("panel");
          panel.innerHTML = "";
          const gatos = await fetch(basePath + "/api/gatos").then(r => r.json());

          for (const gato of gatos) {
            const res = await fetch(`${basePath}/api/gatos/${gato}?summary=true`);
            const data = await res.json();
            const card = document.createElement("div");
            card.className = "gato-card";
            card.innerHTML = `<h2>${gato}</h2><div class="fotos"></div>`;
            const contenedor = card.querySelector(".fotos");

            for (const cam in data.ultimas) {
              const info = data.ultimas[cam];
              if (!info) continue;
              const bloque = document.createElement("div");
              bloque.className = "foto-bloque";
              bloque.innerHTML = `
                <img src="${basePath}/media/${gato}/${info.file}" loading="lazy" title="${info.hora}">
                <div class="camara">${cam}</div>
                <div class="hora">${info.hora}</div>
              `;
              contenedor.appendChild(bloque);
            }

            panel.appendChild(card);
          }
        }

        cargarGatos();
      </script>
    </body>
    </html>
    """)

@app.route("/api/gatos")
def api_gatos():
    if not os.path.exists(CLASIFICADO_DIR):
        return jsonify([])
    return jsonify(sorted([
        d for d in os.listdir(CLASIFICADO_DIR)
        if os.path.isdir(os.path.join(CLASIFICADO_DIR, d))
    ]))

@app.route("/api/gatos/<gato>")
def api_gato(gato):
    carpeta = os.path.join(CLASIFICADO_DIR, gato)
    if not os.path.exists(carpeta):
        return jsonify({"imagenes": [], "ultimas": {}})

    files = sorted([
        f for f in os.listdir(carpeta)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and (gato == "sdg" or "sdg_julieta" not in f)
    ], reverse=True)

    ultimas = {}

    for f in files:
        if "-clean_crop" not in f:
            continue

        camara = f.split("-")[0]  # Detecta la cámara como el primer bloque del nombre

        if camara not in ultimas:
            hora = "?"
            try:
                ts = float(f.split("-")[1])
                hora = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
            except:
                pass
            ultimas[camara] = {"file": f, "hora": hora}

        if len(ultimas) >= 12:
            break

    return jsonify({"ultimas": ultimas} if request.args.get("summary") == "true"
                   else {"imagenes": files, "ultimas": ultimas})

@app.route("/media/<gato>/<filename>")
def media_file(gato, filename):
    path = os.path.join(CLASIFICADO_DIR, gato)
    if os.path.exists(path):
        return send_from_directory(path, filename)
    return abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
