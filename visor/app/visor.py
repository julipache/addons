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
        
def buscar_original(base_name):
    """
    Busca en ORIGINALES_DIR un archivo que empiece con base_name.
    """
    print(f"🔍 Buscando original para base_name: {base_name}")
    try:
        archivos = os.listdir(ORIGINALES_DIR)
        print(f"📂 Archivos en originales: {len(archivos)} encontrados")
        for f in archivos:
            if f.startswith(base_name):
                print(f"✅ Original encontrado: {f}")
                return f
        print("❌ No se encontró original, usando recorte")
    except Exception as e:
        print(f"⚠️ Error buscando original para {base_name}: {e}")
    return None



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
          text-align: center;
          margin-bottom: 10px;
        }
        .gato-name {
          font-size: 1.4em;
          font-weight: bold;
        }
        .ultimas-fotos {
          display: flex;
          flex-wrap: wrap;
          justify-content: space-around;
          margin-top: 10px;
        }
        .foto-bloque {
          text-align: center;
          margin: 5px;
        }
        .foto-bloque img {
          width: 90px;
          height: 90px;
          object-fit: cover;
          border-radius: 8px;
          box-shadow: 0 1px 4px rgba(0,0,0,0.2);
          cursor: pointer;
          transition: transform 0.2s ease;
        }
        .foto-bloque img:hover {
          transform: scale(1.1);
        }
        .foto-tipo {
          font-size: 1em;
          margin: 4px 0;
        }
        .foto-hora {
          font-size: 0.85em;
          color: #666;
        }
        .ver-mas {
          text-align: center;
          margin-top: 10px;
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
            const res = await fetch(`${basePath}/api/gatos/${gato}?summary=true`);
            const data = await res.json();

            const card = document.createElement('div');
            card.className = 'gato-card';

            const header = document.createElement('div');
            header.className = 'gato-header';
            const nombre = document.createElement('div');
            nombre.className = 'gato-name';
            nombre.textContent = gato.charAt(0).toUpperCase() + gato.slice(1);

            const ultimas = document.createElement('div');
            ultimas.className = 'ultimas-fotos';

            const tipos = {
              comio_sala: "🍽️ Sala",
              comio_altillo: "🍽️ Altillo",
              arenero: "🪣 Arenero",
              detectado: "📸 Detectado"
            };

            for (const tipo in tipos) {
              if (!data.ultimas[tipo]) continue;
              const bloque = document.createElement('div');
              bloque.className = 'foto-bloque';
              const label = document.createElement('div');
              label.className = 'foto-tipo';
              label.textContent = tipos[tipo];
              const img = document.createElement('img');
              img.src = `${basePath}/media/${gato}/${data.ultimas[tipo].file}`;
              img.alt = tipo;
              img.loading = "lazy";
              img.onclick = () => openPopup(`${basePath}/originales/${data.ultimas[tipo].original}`); // ✅ Carga original
              const hora = document.createElement('div');
              hora.className = 'foto-hora';
              hora.textContent = data.ultimas[tipo].hora;
              bloque.appendChild(label);
              bloque.appendChild(img);
              bloque.appendChild(hora);
              ultimas.appendChild(bloque);
            }

            const verMas = document.createElement('div');
            verMas.className = 'ver-mas';
            verMas.innerHTML = `<button onclick="openGallery('${gato}')">Ver galería ▶</button>`;

            header.appendChild(nombre);
            card.appendChild(header);
            card.appendChild(ultimas);
            card.appendChild(verMas);

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
        function openGallery(gato) {
          window.location.href = `${basePath}/galeria/${gato}`;
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
        return jsonify({"imagenes": [], "ultimas": {}})

    files = [
        f for f in os.listdir(carpeta)
        if f.lower().endswith(('.jpg', '.png', '.jpeg'))
        and (gato == "sdg" or "sdg_julieta" not in f)
    ]
    files.sort(reverse=True)

    ultimas = {
        "comio_sala": None,
        "comio_altillo": None,
        "arenero": None,
        "detectado": None
    }

    for f in files:
        hora = "?"
        parts = f.split("-")
        if len(parts) > 1:
            try:
                ts = float(parts[1])  # Extraer timestamp UNIX
                dt = datetime.fromtimestamp(ts)
                hora = dt.strftime("%d/%m %H:%M")
            except:
                pass

        base_name = "-".join(f.split("-")[:3])
        original_file = buscar_original(base_name)
        if not original_file:
            print(f"⚠️ Original no encontrado para {f}, usando recorte")
            original_file = f



        if not ultimas["comio_sala"] and "comedero_sala" in f:
            ultimas["comio_sala"] = {"file": f, "original": original_file, "hora": hora}
        elif not ultimas["comio_altillo"] and "altillo" in f:
            ultimas["comio_altillo"] = {"file": f, "original": original_file, "hora": hora}
        elif not ultimas["arenero"] and "arenero" in f:
            ultimas["arenero"] = {"file": f, "original": original_file, "hora": hora}
        elif not ultimas["detectado"]:
            ultimas["detectado"] = {"file": f, "original": original_file, "hora": hora}

        if all(ultimas.values()):
            break

    if request.args.get("summary") == "true":
        return jsonify({"ultimas": ultimas})

    return jsonify({
        "imagenes": files,
        "ultimas": ultimas
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
