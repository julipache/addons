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
      <title>Gatos 🐾</title>
      <style>
        body { font-family: sans-serif; margin: 1em; background: #f0f0f0; }
        .gato { background: white; margin: 1em 0; padding: 1em; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        img { width: 100px; height: 100px; object-fit: cover; border-radius: 6px; margin: 5px; }
      </style>
    </head>
    <body>
      <h1>Panel de gatos 🐾</h1>
      <div id="gatos">Cargando...</div>

      <script>
        const basePath = window.location.pathname.replace(/\\/$/, '');
        const tipos = { comio_sala: "🍽️ Sala", comio_altillo: "🍽️ Altillo", arenero: "🪣 Arenero", detectado: "📸 Detectado" };

        async function cargarGatos() {
          const res = await fetch(basePath + "/api/gatos");
          const gatos = await res.json();
          const contenedor = document.getElementById("gatos");
          contenedor.innerHTML = "";

          for (const gato of gatos) {
            const r = await fetch(`${basePath}/api/gatos/${gato}?summary=true`);
            const data = await r.json();
            const div = document.createElement("div");
            div.className = "gato";
            div.innerHTML = `<h3>${gato}</h3>`;

            for (const tipo in tipos) {
              const info = data.ultimas[tipo];
              if (info) {
                div.innerHTML += `
                  <div>
                    <strong>${tipos[tipo]}</strong><br>
                    <img src="${basePath}/media/${gato}/${info.file}" title="${info.hora}" loading="lazy">
                  </div>`;
              }
            }

            contenedor.appendChild(div);
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

    ultimas = {"comio_sala": None, "comio_altillo": None, "arenero": None, "detectado": None}
    for f in files:
        def set_tipo(clave, tipo):
            if not ultimas[tipo] and clave in f:
                hora = "?"
                try:
                    ts = float(f.split("-")[1])
                    hora = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
                except:
                    pass
                ultimas[tipo] = {"file": f, "hora": hora}

        set_tipo("comedero_sala", "comio_sala")
        set_tipo("altillo", "comio_altillo")
        set_tipo("arenero", "arenero")
        if not ultimas["detectado"]:
            ultimas["detectado"] = {"file": f, "hora": "?"}

        if all(ultimas.values()):
            break

    return jsonify({"ultimas": ultimas} if request.args.get("summary") == "true" else {"imagenes": files, "ultimas": ultimas})

@app.route("/media/<gato>/<filename>")
def media_file(gato, filename):
    path = os.path.join(CLASIFICADO_DIR, gato)
    if os.path.exists(path):
        return send_from_directory(path, filename)
    return abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
