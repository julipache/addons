from flask import Flask, render_template_string, Response
import subprocess
import os

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
        const player1 = new JSMpeg.Player('ws://' + window.location.host + '/video_feed_1', {
            canvas: document.getElementById('videoCanvas1')
        });
        const player2 = new JSMpeg.Player('ws://' + window.location.host + '/video_feed_2', {
            canvas: document.getElementById('videoCanvas2')
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template)

def generate_frames(rtsp_url):
    command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-f', 'mpegts',
        '-codec:v', 'mpeg1video',
        '-bf', '0',
        '-q', '0',
        '-'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        frame = process.stdout.read(1024)
        if not frame:
            break
        yield frame

@app.route('/video_feed_1')
def video_feed_1():
    rtsp_url_1 = os.getenv('RTSP_URL_1')
    return Response(generate_frames(rtsp_url_1), mimetype='video/mp2t')

@app.route('/video_feed_2')
def video_feed_2():
    rtsp_url_2 = os.getenv('RTSP_URL_2')
    return Response(generate_frames(rtsp_url_2), mimetype='video/mp2t')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8099)
