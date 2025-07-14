from flask import Flask, jsonify, send_from_directory, render_template_string, abort
import os

app = Flask(__name__)

# 📂 Rutas
CROPS_DIR = "/media/frigate/clasificado"
ORIGINALS_DIR = "/media/frigate/originales"

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
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }
        h1 { text-align: center; color: #333; margin: 20px 0; }
        .container { display: flex; flex-direction: column; align-items: center; padding: 10px; }
        .gato-card { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); width: 95%; max-width: 800px; margin: 10px 0; padding: 15px; }
        .gato-name { font-size: 1.6em; font-weight: bold; text-align: center; color: #444; margin-bottom: 10px; }
        .galeria { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        .foto-container { display: flex; flex-direction: column; align-items: center; width: 150px; }
        .galeria img { width: 100%; border-radius: 8px; object-fit: cover; box-shadow: 0 1px 4px rgba(0,0,0,0.2); transition: transform 0.2s ease; }
        .galeria img:hover { transform: scale(1.05); }
        .foto-info { font-size: 0.85em; text-align: center; color: #777; margin-top: 4px; }
        .original-link { font-size: 0.8em; color: #007bff; text-decoration: underline; cursor: pointer; margin-top: 2px; }
        .original-link:hover { color: #0056b3; }
      </style>
    </head>
    <body>
      <h1>Panel de gatos 🐾</h1>
      <div class="container" id="gatos"></div>
      <script>
        const basePath = window.location.pathname.replace(/\\/$/, '');
        fetch(`${basePath}/api/gatos`)
          .then(res => res.json())
          .then(gatos => {
            const container = document.getElementById('gatos');
            if (!gatos.length) {
              container.innerHTML = '<div class="foto-info">No hay fotos clasificadas aún 🐱</div>';
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

                  if (!imagenes.length) {
                    const empty = document.createElement('div');
                    empty.className = 'foto-info';
                    empty.textContent = 'No hay fotos para este gato 🐾';
                    galeria.appendChild(empty);
                  } else {
                    imagenes.slice(0, 10).forEach(imgName => {
                      const imgUrl = `${basePath}/media/${gato}/${imgName}`;
                      const originalName = imgName.replace('_crop', ''); // quitar _crop para buscar el original
                      const originalUrl = `${basePath}/original/${originalName}`;

                      const containerImg = document.createElement('div');
                      containerImg.className = 'foto-container';

                      const img = document.createElement('img');
                      img.src = imgUrl;
                      img.alt = gato;

                      const info = document.createElement('div');
                      info.className = 'foto-info';
                      info.textContent = imgName.includes('comio') ? '🍽️ Comió' :
                                         imgName.includes('arenero') ? '🪣 Arenero' :
                                         '📸 Detectado';

                      const link = document.createElement('div');
                      link.className = 'original-link';
                      link.textContent = 'Ver original';
                      link.onclick = () => window.open(originalUrl, '_blank');

                      containerImg.appendChild(img);
                      containerImg.appendChild(info);
                      containerImg.appendChild(link);

                      galeria.appendChild(containerImg);
                    });
                  }

                  card.appendChild(nombre);
                  card.appendChild(galeria);
                  container.appendChild(card);
                });
            });
          });
      </script>
    </body>
    </html>
    """)

@app.route("/api/gatos")
def lista_gatos():
    if not os.path.exists(CROPS_DIR):
        return jsonify([])
    gatos = [d for d in os.listdir(CROPS_DIR) if os.path.isdir(os.path.join(CROPS_DIR, d))]
    return jsonify(gatos)

@app.route("/api/gatos/<gato>")
def lista_imagenes(gato):
    carpeta = os.path.join(CROPS_DIR, gato)
    if not os.path.exists(carpeta):
        return jsonify([])
    imagenes = sorted([f for f in os.listdir(carpeta) if f.lower().endswith(('.jpg', '.png', '.jpeg'))], reverse=True)
    return jsonify(imagenes)

@app.route("/media/<gato>/<filename>")
def serve_crop(gato, filename):
    carpeta = os.path.join(CROPS_DIR, gato)
    if not os.path.exists(carpeta):
        abort(404)
    return send_from_directory(carpeta, filename)

@app.route("/original/<filename>")
def serve_original(filename):
    carpeta = ORIGINALS_DIR
    if not os.path.exists(os.path.join(carpeta, filename)):
        abort(404)
    return send_from_directory(carpeta, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
