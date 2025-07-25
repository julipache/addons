from flask import Flask, jsonify, send_from_directory, render_template_string, request, abort
import os
from datetime import datetime

app = Flask(__name__)

CLASIFICADO_DIR = "/media/frigate/clasificado"
ORIGINALES_DIR = "/media/frigate/originales"

@app.before_request
def adjust_ingress_path():
    ingress_path = request.headers.get("X-Ingress-Path")
    if ingress_path:
        app.url_map.script_name = ingress_path

def buscar_original(base_name):
    try:
        return next((f for f in os.listdir(ORIGINALES_DIR) if f.startswith(base_name)), None)
    except Exception as e:
        print(f"❌ Error buscando original: {e}")
        return None

@app.route("/")
def index():
    return render_template_string("""
    <html><head><title>Gatos</title></head>
    <body><h1>Panel de gatos 🐾</h1><div id="panel"></div>
    <script>
      fetch("api/gatos").then(r => r.json()).then(async gatos => {
        const panel = document.getElementById("panel");
        if (!gatos.length) return panel.innerHTML = "No hay gatos";
        for (let g of gatos) {
          const d = await fetch(`api/gatos/${g}?summary=true`).then(r => r.json());
          panel.innerHTML += `<h2>${g}</h2>` + Object.entries(d.ultimas).map(([k, v]) =>
            v ? `<img src="/media/${g}/${v.file}" width="100"><small>${v.hora}</small>` : ''
          ).join('');
        }
      });
    </script></body></html>
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
def api_imagenes(gato):
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
        base = "-".join(f.split("-")[:3])
        original = buscar_original(base) or f
        hora = "?"
        try:
            ts = float(f.split("-")[1])
            hora = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
        except: pass

        def set_if_none(key, substr):
            if not ultimas[key] and substr in f:
                ultimas[key] = {"file": f, "original": original, "hora": hora}

        set_if_none("comio_sala", "comedero_sala")
        set_if_none("comio_altillo", "altillo")
        set_if_none("arenero", "arenero")
        if not ultimas["detectado"]:
            ultimas["detectado"] = {"file": f, "original": original, "hora": hora}

        if all(ultimas.values()):
            break

    return jsonify({"ultimas": ultimas} if request.args.get("summary") == "true"
                   else {"imagenes": files, "ultimas": ultimas})

@app.route("/media/<gato>/<filename>")
def media(gato, filename):
    path = os.path.join(CLASIFICADO_DIR, gato)
    return send_from_directory(path, filename) if os.path.exists(path) else abort(404)

@app.route("/originales/<filename>")
def originales(filename):
    return send_from_directory(ORIGINALES_DIR, filename) if os.path.exists(ORIGINALES_DIR) else abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
