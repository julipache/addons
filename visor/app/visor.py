from flask import Flask, jsonify, send_from_directory, render_template_string, abort, request
import os
from datetime import datetime

app = Flask(__name__)

# 📂 Rutas a carpetas
CLASIFICADO_DIR = "/media/frigate/clasificado"
ORIGINALES_DIR = "/media/frigate/originales"

@app.before_request
def adjust_ingress_path():
    ingress_path = request.headers.get("X-Ingress-Path")
    if ingress_path:
        app.url_map.script_name = ingress_path

def buscar_original(base_name):
    """
    Buscar en la carpeta de originales un archivo que empiece con base_name
    """
    try:
        for f in os.listdir(ORIGINALES_DIR):
            if f.startswith(base_name):
                return f
    except Exception as e:
        print(f"Error buscando original: {e}")
    return None

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Panel de gatos 🐾</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial, sans-serif; background: #f0f0f0; margin: 0; }
        h1 { text-align: center; margin: 20px; }
        .container { display: flex; flex-direction: column; align-items: center; }
        .error { color: red; margin: 20px; }
        .gato-card { background: white; margin: 10px; padding: 10px; border-radius: 10px; width: 90%; max-width: 600px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .gato-name { font-size: 1.4em; font-weight: bold; margin-bottom: 10px; }
        .ultimas-fotos { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
        .foto-bloque img { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; }
      </style>
    </head>
    <body>
      <h1>Panel de gatos 🐾</h1>
      <div id="container" class="container"></div>
      <script>
        async function loadGatos() {
          const container = document.getElementById("container");
          try {
            const res = await fetch("./api/gatos");
            if (!res.ok) throw new Error("API /api/gatos no responde");
            const gatos = await res.json();
            if (gatos.length === 0) {
              container.innerHTML = "<div class='error'>No se encontraron carpetas de gatos 🐱</div>";
              return;
            }
            gatos.forEach(async (gato) => {
              try {
                const r = await fetch(`./api/gatos/${gato}?summary=true`);
                if (!r.ok) throw new Error(`Error cargando datos de ${gato}`);
                const data = await r.json();
                const card = document.createElement("div");
                card.className = "gato-card";
                const name = document.createElement("div");
                name.className = "gato-name";
                name.textContent = gato;
                const fotos = document.createElement("div");
                fotos.className = "ultimas-fotos";
                Object.entries(data.ultimas).forEach(([tipo, info]) => {
                  if (!info) return;
                  const img = document.createElement("img");
                  img.src = `./media/${gato}/${info.file}`;
                  img.title = `${tipo} (${info.hora})`;
                  fotos.appendChild(img);
                });
                card.appendChild(name);
                card.appendChild(fotos);
                container.appendChild(card);
              } catch (e) {
                console.error(e);
              }
            });
          } catch (e) {
            console.error(e);
            container.innerHTML = "<div class='error'>Error cargando datos: " + e.message + "</div>";
          }
        }
        loadGatos();
      </script>
    </body>
    </html>
    """)


@app.route("/api/gatos")
def lista_gatos():
    if not os.path.exists(CLASIFICADO_DIR):
        print("⚠️ Carpeta clasificado no encontrada:", CLASIFICADO_DIR)
        return jsonify([])
    gatos = [d for d in os.listdir(CLASIFICADO_DIR) if os.path.isdir(os.path.join(CLASIFICADO_DIR, d))]
    print("✅ Encontrados gatos:", gatos)
    return jsonify(sorted(gatos))


@app.route("/api/gatos/<gato>")
def lista_imagenes(gato):
    carpeta = os.path.join(CLASIFICADO_DIR, gato)
    if not os.path.exists(carpeta):
        print(f"⚠️ Carpeta no encontrada para {gato}")
        return jsonify({"imagenes": [], "ultimas": {}})
    files = sorted(os.listdir(carpeta), reverse=True)
    ultimas = {}
    for f in files:
        hora = "?"
        parts = f.split("-")
        if len(parts) > 1:
            try:
                ts = float(parts[1])
                hora = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
            except:
                pass
        base_name = "-".join(parts[:3])  # Hasta wpmple
        original = buscar_original(base_name) or f
        if "comio" in f and not ultimas.get("comio"):
            ultimas["comio"] = {"file": f, "original": original, "hora": hora}
        elif "arenero" in f and not ultimas.get("arenero"):
            ultimas["arenero"] = {"file": f, "original": original, "hora": hora}
        elif not ultimas.get("detectado"):
            ultimas["detectado"] = {"file": f, "original": original, "hora": hora}
        if len(ultimas) == 3:
            break
    return jsonify({"ultimas": ultimas})


@app.route("/media/<gato>/<filename>")
def serve_recorte(gato, filename):
    carpeta = os.path.join(CLASIFICADO_DIR, gato)
    if not os.path.exists(carpeta):
        abort(404)
    return send_from_directory(carpeta, filename)


@app.route("/originales/<filename>")
def serve_original(filename):
    if not os.path.exists(ORIGINALES_DIR):
        abort(404)
    return send_from_directory(ORIGINALES_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
