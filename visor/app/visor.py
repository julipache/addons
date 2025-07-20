from flask import Flask, jsonify, send_from_directory, render_template_string, abort, request
import os
from datetime import datetime

app = Flask(__name__)

# 📂 Rutas a carpetas
CLASIFICADO_DIR = "/media/frigate/clasificado"
ORIGINALES_DIR = "/media/frigate/originales"

# 🔄 Ajustar rutas para Home Assistant ingress
@app.before_request
def adjust_ingress_path():
    ingress_path = request.headers.get("X-Ingress-Path")
    if ingress_path:
        app.url_map.script_name = ingress_path


@app.route("/")
def index():
    if not os.path.exists(CLASIFICADO_DIR):
        return "<h2>Error: No se encuentra la carpeta de imágenes 🐾</h2>", 500

    # 🖤 Modo oscuro + filtros + contadores
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Panel de gatos 🐾</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body {
          font-family: Arial, sans-serif;
          background: #f5f5f5;
          color: #333;
          margin: 0; padding: 0;
        }
        @media (prefers-color-scheme: dark) {
          body { background: #121212; color: #eee; }
          .gato-card { background: #1e1e1e; box-shadow: 0 2px 8px rgba(255,255,255,0.1); }
        }
        h1 { text-align: center; margin: 20px 0; }
        .container { display: flex; flex-direction: column; align-items: center; padding: 10px; }
        .gato-card {
          background: #fff;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
          width: 95%;
          max-width: 800px;
          margin: 10px 0;
          padding: 15px;
        }
        .gato-name {
          font-size: 1.6em;
          font-weight: bold;
          text-align: center;
          margin-bottom: 10px;
        }
        .gato-stats {
          text-align: center;
          font-size: 0.95em;
          margin-bottom: 10px;
        }
        .galeria {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          justify-content: center;
        }
        .galeria img {
          height: 120px;
          border-radius: 8px;
          object-fit: cover;
          box-shadow: 0 1px 4px rgba(0,0,0,0.2);
          cursor: pointer;
          transition: transform 0.2s ease;
        }
        .galeria img:hover {
          transform: scale(1.05);
        }
        .foto-info {
          text-align: center;
          font-size: 0.85em;
          color: #777;
        }
        .empty-msg {
          text-align: center;
          color: #999;
          margin-top: 30px;
          font-size: 1.2em;
        }
        #filter-container {
          text-align: center;
          margin: 10px;
        }
        select {
          padding: 5px 10px;
          border-radius: 8px;
        }
        .popup {
          display: none;
          position: fixed;
          top: 0; left: 0; width: 100%; height: 100%;
          background: rgba(0,0,0,0.8);
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }
        .popup img {
          max-width: 90%; max-height: 90%;
          border-radius: 12px;
        }
      </style>
    </head>
    <body>
      <h1>Panel de gatos 🐾</h1>

      <div id="filter-container">
        <label for="dateFilter">📅 Filtrar por:</label>
        <select id="dateFilter" onchange="loadGatos()">
          <option value="all">Todas</option>
          <option value="today">Hoy</option>
          <option value="24h">Últimas 24h</option>
        </select>
      </div>

      <div class="container" id="gatos"></div>

      <div id="popup" class="popup" onclick="closePopup()">
        <img id="popupImg" src="">
      </div>

      <script>
        const basePath = window.location.pathname.replace(/\\/$/, '');
        async function loadGatos() {
          const filter = document.getElementById('dateFilter').value;
          const res = await fetch(`${basePath}/api/gatos`);
          const gatos = await res.json();
          const container = document.getElementById('gatos');
          container.innerHTML = '';

          if (!gatos.length) {
            container.innerHTML = '<div class="empty-msg">No hay fotos clasificadas aún 🐱</div>';
            return;
          }

          gatos.forEach(async (gato) => {
            const res = await fetch(`${basePath}/api/gatos/${gato}?filter=${filter}`);
            const data = await res.json();

            const card = document.createElement('div');
            card.className = 'gato-card';

            const nombre = document.createElement('div');
            nombre.className = 'gato-name';
            nombre.textContent = gato.charAt(0).toUpperCase() + gato.slice(1);

            const stats = document.createElement('div');
            stats.className = 'gato-stats';
            stats.innerHTML = `🍽️ ${data.stats.comio} 🪣 ${data.stats.arenero} 📸 ${data.stats.detectado}<br>
                               🕒 Última actividad: ${data.stats.ultima_foto}`;

            const galeria = document.createElement('div');
            galeria.className = 'galeria';

            data.imagenes.forEach(imgName => {
              const imgUrl = `${basePath}/media/${gato}/${imgName}`;
              const originalUrl = `${basePath}/originales/${imgName}`;
              const img = document.createElement('img');
              img.src = imgUrl;
              img.alt = gato;
              img.onclick = () => openPopup(originalUrl);
              galeria.appendChild(img);
            });

            card.appendChild(nombre);
            card.appendChild(stats);
            card.appendChild(galeria);
            container.appendChild(card);
          });
        }

        function openPopup(url) {
          document.getElementById('popupImg').src = url;
          document.getElementById('popup').style.display = 'flex';
        }
        function closePopup() {
          document.getElementById('popup').style.display = 'none';
        }

        loadGatos();
        setInterval(loadGatos, 300000); // 🔄 Auto-refresh cada 5 min
      </script>
    </body>
    </html>
    """)


@app.route("/api/gatos")
def lista_gatos():
    if not os.path.exists(CLASIFICADO_DIR):
        return jsonify([])
    gatos = [d for d in os.listdir(CLASIFICADO_DIR) if os.path.isdir(os.path.join(CLASIFICADO_DIR, d))]
    return jsonify(sorted(gatos))


@app.route("/api/gatos/<gato>")
def lista_imagenes(gato):
    carpeta = os.path.join(CLASIFICADO_DIR, gato)
    if not os.path.exists(carpeta):
        return jsonify({"imagenes": [], "stats": {}})

    filter_mode = request.args.get("filter", "all")
    imagenes = [
        f for f in os.listdir(carpeta)
        if f.lower().endswith(('.jpg', '.png', '.jpeg'))
        and (gato == "sdg" or "sdg_julieta" not in f)  # ❌ Filtrar sdg_julieta
    ]
    imagenes.sort(reverse=True)

    # 📊 Contadores
    comio = sum(1 for f in imagenes if "comio" in f.lower())
    arenero = sum(1 for f in imagenes if "arenero" in f.lower())
    detectado = len(imagenes)
    ultima_foto = imagenes[0] if imagenes else "N/A"
    ultima_foto_time = ultima_foto.split("_")[0] if "_" in ultima_foto else "N/A"

    # 🗓️ Filtrar por fecha
    if filter_mode != "all":
        now = datetime.now()
        filtered = []
        for img in imagenes:
            try:
                ts_str = img.split("_")[0]
                ts = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                if filter_mode == "today" and ts.date() == now.date():
                    filtered.append(img)
                elif filter_mode == "24h" and (now - ts).total_seconds() <= 86400:
                    filtered.append(img)
            except:
                continue
        imagenes = filtered

    return jsonify({
        "imagenes": imagenes,
        "stats": {
            "comio": comio,
            "arenero": arenero,
            "detectado": detectado,
            "ultima_foto": ultima_foto_time
        }
    })


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
