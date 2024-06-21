from flask import Flask, render_template_string, Response
import os
import threading
import subprocess
import websockets
import asyncio

app = Flask(__name__)

# Template HTML para mostrar las cámaras
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTSP Cameras</title>
    <script src="https://cdn.jsdelivr.net/npm/jsmpeg@0.2/jsmpeg.min.js"></script>
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

async def stream_rtsp(rtsp_url, websocket):
    command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-f', 'mpegts',
        '-codec:v', 'mpeg1video',
        '-bf', '0',
        '-q', '0',
        '-r', '30',
        '-'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        frame = process.stdout.read(1024)
        if not frame:
            break
        await websocket.send(frame)
    process.stdout.close()
    process.wait()

async def ws_handler(websocket, path):
    rtsp_url = os.getenv('RTSP_URL_1') if path == '/video_feed_1' else os.getenv('RTSP_URL_2')
    await stream_rtsp(rtsp_url, websocket)

def start_ws_server(port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(ws_handler, '0.0.0.0', port)
    loop.run_until_complete(server)
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=start_ws_server, args=(8081,)).start()
    threading.Thread(target=start_ws_server, args=(8082,)).start()
    app.run(host='0.0.0.0', port=8099)
