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
    <html><body style="font-family:sans-serif">
    <h1>Gatos 🐾</h1><div id="panel"></div>
    <script>
    fetch("api/gatos").then(r => r.json()).then(async gatos => {
      const panel = document.getElementById("panel");
      for (let g of gatos) {
        const res = await fetch(`api/gatos/${g}?summary=true`);
        const data = await res.json();
        const card = document.createElement("div");
        card.innerHTML = `<h3>${g}</h3>` + Object.values(data.ultimas).map(
          v => v ? `<img src="/media/${g}/${v.file}" width="100">` : ''
        ).join("");
        panel.appendChild(card);
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
        def set(tipo, clave):
            if not ultimas[tipo] and clave in f:
                hora = "?"
                try:
                    ts = float(f.split("-")[1])
                    hora = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
                except: pass
                ultimas[tipo] = {"file": f, "hora": hora}

        set("comio_sala", "comedero_sala")
        set("comio_altillo", "altillo")
        set("arenero", "arenero")
        if not ultimas["detectado"]:
            ultimas["detectado"] = {"file": f, "hora": "?"}

        if all(ultimas.values()):
            break

    return jsonify({"ultimas": ultimas} if request.args.get("summary") == "true"
                   else {"imagenes": files, "ultimas": ultimas})

@app.route("/media/<gato>/<filename>")
def media(gato, filename):
    carpeta = os.path.join(CLASIFICADO_DIR, gato)
    return send_from_directory(carpeta, filename) if os.path.exists(carpeta) else abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
