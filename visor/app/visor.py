from flask import Flask, jsonify, send_from_directory, render_template_string, request, abort
import os

app = Flask(__name__)

# 📂 Ruta donde están clasificadas las fotos de gatos
MEDIA_DIR = "/media/frigate/clasificado"

# 🛡️ Token opcional (lo dejamos vacío porque Home Assistant ya controla acceso con ingress)
AUTH_TOKEN = ""  # Si quieres añadir uno extra, pon algo como "mipasswordsegura"

# 🌐 HTML para la galería
html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Panel de gatos 🐾</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 20px; }
    h1 { text-align: center; margin-bottom: 30px; }
    .gato-card {
      background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 15px; margin: 20px auto; max-width: 800px;
    }
    .gato-name { font-size: 1.8em; font-weight: bold; text-align: center; margin-bottom: 10px; }
    .galeria { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; }
    .galeria img { height: 150px; border-radius: 8px; flex-shrink: 0; object-fit: cover; box-shadow: 0 1px 4px rgba(0,0,0,0.2); }
    .foto-info { font-size: 0.9em; text-align: center; color: #666; margin-top: 4px; }
  </style>
</head>
<body>
  <h1>Panel de gatos 🐾</h1>
  <div id="gatos"></div>
  <script>
    fetch('/api/gatos')
      .then(res => res.json())
      .then(gatos => {
        gatos.forEach(gato => {
          fetch(`/api/gatos/${gato}`)
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
                const imgUrl = `/media/${gato}/${imgName}`;
                const img = document.createElement('img');
                img.src = imgUrl;
                img.alt = gato;

                const info = document.createElement('div');
                info.className = 'foto-info';
                const accion = imgName.includes('comio') ? '🍽️ Comió' :
                               imgName.includes('arenero') ? '🪣 Arenero' :
                               '📸 Detectado';
                info.textContent = accion;

                const container = document.createElement('div');
                container.style.textAlign = 'center';
                container.appendChild(img);
                container.appendChild(info);

                galeria.appendChild(container);
              });

              card.appendChild(nombre);
              card.appendChild(galeria);
              document.getElementById('gatos').appendChild(card);
            });
        });
      });
  </script>
</body>
</html>
"""

# 🔐 (opcional) Middleware de autenticación
@app.before_request
def check_auth():
    if AUTH_TOKEN and request.headers.get('Authorization') != f"Bearer {AUTH_TOKEN}":
        abort(401)

@app.route("/")
def index():
    return render_template_string(html_template)

@app.route("/api/gatos")
def lista_gatos():
    gatos = [d for d in os.listdir(MEDIA_DIR) if os.path.isdir(os.path.join(MEDIA_DIR, d))]
    return jsonify(gatos)

@app.route("/api/gatos/<gato>")
def lista_imagenes(gato):
    carpeta = os.path.join(MEDIA_DIR, gato)
    if not os.path.exists(carpeta):
        abort(404)
    imagenes = sorted([f for f in os.listdir(carpeta) if f.lower().endswith(('.jpg', '.png', '.jpeg'))], reverse=True)
    return jsonify(imagenes)

@app.route("/media/<gato>/<filename>")
def serve_image(gato, filename):
    carpeta = os.path.join(MEDIA_DIR, gato)
    return send_from_directory(carpeta, filename)

if __name__ == "__main__":
    # ⚡ Escuchar en todas las interfaces, necesario para ingress
    app.run(host="0.0.0.0", port=8099)
