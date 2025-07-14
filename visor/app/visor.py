<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Panel de gatos</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
    h1 { text-align: center; color: #333; }
    .gato-container {
      display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;
    }
    .gato-card {
      background: #fff; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      padding: 10px; width: 250px; text-align: center;
    }
    .gato-card img {
      width: 100%; height: auto; border-radius: 8px; object-fit: cover;
    }
    .gato-name {
      font-size: 1.3em; font-weight: bold; margin: 10px 0; color: #007bff;
    }
    .gato-info {
      color: #555; font-size: 0.9em;
    }
  </style>
</head>
<body>
  <h1>🐱 Panel de gatos</h1>
  <p style="text-align:center;">Selecciona la carpeta raíz donde están las carpetas de cada gato:</p>
  <div style="text-align:center; margin-bottom: 20px;">
    <input type="file" webkitdirectory directory multiple onchange="loadGatos(event)">
  </div>
  <div id="gatos" class="gato-container"></div>

  <script>
    function loadGatos(event) {
      const files = event.target.files;
      const gatos = {};

      // Agrupa las imágenes por carpeta
      Array.from(files).forEach(file => {
        const pathParts = file.webkitRelativePath.split('/');
        if (pathParts.length >= 2 && file.type.startsWith('image/')) {
          const gatoName = pathParts[1];
          if (!gatos[gatoName]) gatos[gatoName] = [];
          gatos[gatoName].push({
            name: file.name,
            url: URL.createObjectURL(file)
          });
        }
      });

      const container = document.getElementById('gatos');
      container.innerHTML = '';

      // Muestra cada gato
      Object.entries(gatos).forEach(([gatoName, images]) => {
        // Ordena imágenes por nombre (asume que tienen fecha en el nombre)
        images.sort((a, b) => b.name.localeCompare(a.name)); // más reciente primero
        const latestImage = images[0].url;

        const card = document.createElement('div');
        card.className = 'gato-card';
        card.innerHTML = `
          <img src="${latestImage}" alt="${gatoName}">
          <div class="gato-name">${gatoName}</div>
          <div class="gato-info">Última foto: ${images[0].name}</div>
        `;
        container.appendChild(card);
      });
    }
  </script>
</body>
</html>
