from flask import Flask, jsonify, send_from_directory, render_template_string, abort, request
import os

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

    # 🔥 HTML dinámico con galería y popup
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Panel de gatos 🐾</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }
        h1 { text-align: center; color: #333; margin: 20px 0; }
        .container { display: flex; flex-direction: column; align-items: center; padding: 10px; }
        .gato-card { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); width: 95%; max-width: 800px; margin: 10px 0; padding: 15px; }
        .gato-name { font-size: 1.6em; font-weight: bold; text-align: center; color: #444; margin-bottom: 10px; }
        .galeria { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; }
        .galeria img { height: 120px; border-radius: 8px; flex-shrink: 0; object-fit: cover; box-shadow: 0 1px 4px rgba(0,0,0,0.2); transition: transform 0.2s ease; cursor: pointer; }
        .galeria img:hover { transform: scale(1.05); }
        .foto-info { font-size: 0.85em; text-align: center; color: #777; margin-top: 4px; }
        .empty-msg { text-align: center; color: #999; margin-top: 30px; font-size: 1.2em; }
        /* Popup */
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
          border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
      </style>
    </head>
    <body>
      <h1>Panel de gatos 🐾</h1>
      <div class="container" id="gatos"></div>

      <!-- Popup para foto original -->
      <div id="popup" class="popup" onclick="closePopup()">
        <img id="popupImg" src="">
      </div>

      <script>
        const basePath = window.location.pathname.replace(/\\/$/, '');
        fetch(`${basePath}/api/gatos`)
          .then(res => res.json())
          .then(gatos => {
            const container = document.getElementById('gatos');
            if (!gatos.length) {
              container.innerHTML = '<div class="empty-msg">No hay fotos clasificadas aún 🐱</div>';
              return;
            }
            gatos.forEach(gato => {
              fetch(`${basePath}/api/gatos/${gato}`)
                .then(res => res.json())
                .then(imagenes => {
                  const card = document.createElement('div');
                  card.className = 'gato-card';

                  const nombre = document.createElement('div');
                  nombre.className = 'gato-name';
                  nombre.textContent = gato.charAt(0).toUpperCase() + gato.slice(1);

                  const galeria = document.createElement('div');
                  galeria.className = 'galeria';

                  imagenes.slice(0, 10).forEach(imgName => {
                    const imgUrl = `${basePath}/media/${gato}/${imgName}`;
                    const originalUrl = `${basePath}/originales/${imgName}`;
                    const img = document.createElement('img');
                    img.src = imgUrl;
                    img.alt = gato;

                    img.onclick = () => openPopup(originalUrl);

                    const info = document.createElement('div');
                    info.className = 'foto-info';
                    const accion = imgName.includes('comio') ? '🍽️ Comió' :
                                   imgName.includes('arenero') ? '🪣 Arenero' :
                                   '📸 Detectado';
                    info.textContent = accion;

                    const containerImg = document.createElement('div');
                    containerImg.style.textAlign = 'center';
                    containerImg.appendChild(img);
                    containerImg.appendChild(info);

                    galeria.appendChild(containerImg);
                  });

                  card.appendChild(nombre);
                  card.appendChild(galeria);
                  container.appendChild(card);
                });
            });
          });

        function openPopup(url) {
          const popup = document.getElementById('popup');
          const popupImg = document.getElementById('popupImg');
          popupImg.src = url;
          popup.style.display = 'flex';
        }

        function closePopup() {
          document.getElementById('popup').style.display = 'none';
        }
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
        return jsonify([])
    imagenes = [
        f for f in os.listdir(carpeta)
        if f.lower().endswith(('.jpg', '.png', '.jpeg'))
        and (gato == "sdg" or "sdg_julieta" not in f)  # ❌ Filtrar sdg_julieta
    ]
    imagenes.sort(reverse=True)
    return jsonify(imagenes)

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
