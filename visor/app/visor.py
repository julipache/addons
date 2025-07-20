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
        .gato-header {
          display: flex; justify-content: space-between; align-items: center;
          cursor: pointer; user-select: none;
        }
        .gato-name {
          font-size: 1.4em;
          font-weight: bold;
        }
        .gato-stats {
          font-size: 0.9em;
          color: #666;
        }
        .galeria {
          display: none;
          flex-wrap: wrap;
          gap: 8px;
          justify-content: center;
          margin-top: 10px;
        }
        .galeria img {
          height: 100px;
          border-radius: 8px;
          object-fit: cover;
          box-shadow: 0 1px 4px rgba(0,0,0,0.2);
          cursor: pointer;
          transition: transform 0.2s ease;
        }
        .galeria img:hover {
          transform: scale(1.05);
        }
        .ver-mas {
          text-align: center;
          margin: 10px 0;
        }
        .ver-mas button {
          padding: 6px 12px;
          border: none;
          border-radius: 6px;
          background: #007bff;
          color: #fff;
          cursor: pointer;
        }
        .ver-mas button:hover {
          background: #0056b3;
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
      <div class="container" id="gatos"></div>

      <div id="popup" class="popup" onclick="closePopup()">
        <img id="popupImg" src="">
      </div>

      <script>
        const basePath = window.location.pathname.replace(/\\/$/, '');

        async function loadGatos() {
          const res = await fetch(`${basePath}/api/gatos`);
          const gatos = await res.json();
          const container = document.getElementById('gatos');
          container.innerHTML = '';

          if (!gatos.length) {
            container.innerHTML = '<div class="empty-msg">No hay fotos clasificadas aún 🐱</div>';
            return;
          }

          gatos.forEach(async (gato) => {
            const res = await fetch(`${basePath}/api/gatos/${gato}?page=1&per_page=10`);
            const data = await res.json();

            const card = document.createElement('div');
            card.className = 'gato-card';

            const header = document.createElement('div');
            header.className = 'gato-header';
            header.onclick = () => toggleGaleria(gato);

            const nombre = document.createElement('div');
            nombre.className = 'gato-name';
            nombre.textContent = gato.charAt(0).toUpperCase() + gato.slice(1);

            const stats = document.createElement('div');
            stats.className = 'gato-stats';
            stats.innerHTML = `🍽️ ${data.stats.comio} 🪣 ${data.stats.arenero} 📸 ${data.stats.detectado}<br>
                               🕒 Última: ${data.stats.ultima_foto}`;

            header.appendChild(nombre);
            header.appendChild(stats);

            const galeria = document.createElement('div');
            galeria.className = 'galeria';
            galeria.id = `galeria-${gato}`;
            galeria.dataset.page = 1;

            data.imagenes.forEach(imgName => {
              const imgUrl = `${basePath}/media/${gato}/${imgName}`;
              const originalUrl = `${basePath}/originales/${imgName}`;
              const img = document.createElement('img');
              img.src = imgUrl;
              img.alt = gato;
              img.loading = "lazy";
              img.onclick = () => openPopup(originalUrl);
              galeria.appendChild(img);
            });

            const verMas = document.createElement('div');
            verMas.className = 'ver-mas';
            verMas.innerHTML = `<button onclick="loadMore('${gato}')">Ver más</button>`;

            galeria.appendChild(verMas);

            card.appendChild(header);
            card.appendChild(galeria);
            container.appendChild(card);
          });
        }

        function toggleGaleria(gato) {
          const galeria = document.getElementById(`galeria-${gato}`);
          galeria.style.display = galeria.style.display === 'flex' ? 'none' : 'flex';
        }

        async function loadMore(gato) {
          const galeria = document.getElementById(`galeria-${gato}`);
          let page = parseInt(galeria.dataset.page) + 1;
          const res = await fetch(`${basePath}/api/gatos/${gato}?page=${page}&per_page=10`);
          const data = await res.json();

          if (!data.imagenes.length) {
            galeria.querySelector('.ver-mas').innerHTML = "<i>No hay más fotos</i>";
            return;
          }

          data.imagenes.forEach(imgName => {
            const imgUrl = `${basePath}/media/${gato}/${imgName}`;
            const originalUrl = `${basePath}/originales/${imgName}`;
            const img = document.createElement('img');
            img.src = imgUrl;
            img.alt = gato;
            img.loading = "lazy";
            img.onclick = () => openPopup(originalUrl);
            galeria.insertBefore(img, galeria.querySelector('.ver-mas'));
          });

          galeria.dataset.page = page;
        }

        function openPopup(url) {
          document.getElementById('popupImg').src = url;
          document.getElementById('popup').style.display = 'flex';
        }
        function closePopup() {
          document.getElementById('popup').style.display = 'none';
        }

        loadGatos();
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

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

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

    # 📦 Paginación
    start = (page - 1) * per_page
    end = start + per_page
    imagenes_pag = imagenes[start:end]

    return jsonify({
        "imagenes": imagenes_pag,
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
