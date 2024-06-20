from flask import Flask, render_template_string, request
import os
import threading
import subprocess
import websocket_server

app = Flask(__name__)

# Template HTML para mostrar las cámaras
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTSP Cameras</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jsmpeg/0.2/jsmpeg.min.js"></script>
</head>
<body>
    <h1>RTSP Cameras</h1>
    <div>
        <canvas id="videoCanvas1" width="640" height="480"></canvas>
        <canvas id="videoCanvas2" width="640" height="480"></canvas>
        <!-- Puedes añadir más streams aquí -->
    </div>
    <script>
        const player1 = new JSMpeg.Player('ws://' + window.location.hostname + ':8081', {
            canvas: document.getElementById('videoCanvas1')
        });
        const player2 = new JSMpeg.Player('ws://' + window.location.hostname + ':8082', {
            canvas: document.getElementById('videoCanvas2')
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template)

def start_stream(rtsp_url, ws_port):
    command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-f', 'mpegts',
        '-codec:v', 'mpeg1video',
        '-bf', '0',
        '-q', '0',
        '-r', '30',
        'http://127.0.0.1:' + str(ws_port)
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()

def run_websocket_server(port):
    server = websocket_server.WebSocketServer('', port)
    server.run_forever()

if __name__ == "__main__":
    rtsp_url_1 = os.getenv('RTSP_URL_1')
    rtsp_url_2 = os.getenv('RTSP_URL_2')

    threading.Thread(target=run_websocket_server, args=(8081,)).start()
    threading.Thread(target=run_websocket_server, args=(8082,)).start()

    threading.Thread(target=start_stream, args=(rtsp_url_1, 8081)).start()
    threading.Thread(target=start_stream, args=(rtsp_url_2, 8082)).start()

    app.run(host='0.0.0.0', port=8099)
