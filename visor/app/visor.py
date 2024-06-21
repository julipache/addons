from flask import Flask, Response, render_template_string
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
</head>
<body>
    <h1>RTSP Cameras</h1>
    <div>
        <img src="/video_feed_1" width="640" height="480">
        <img src="/video_feed_2" width="640" height="480">
        <!-- Puedes añadir más streams aquí -->
    </div>
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
        '-vf', 'fps=15',
        '-f', 'mjpeg',
        '-q:v', '2',
        '-'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        frame = process.stdout.read(1024)
        if not frame:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    process.stdout.close()
    process.wait()

@app.route('/video_feed_1')
def video_feed_1():
    rtsp_url_1 = os.getenv('RTSP_URL_1')
    return Response(generate_frames(rtsp_url_1),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_2')
def video_feed_2():
    rtsp_url_2 = os.getenv('RTSP_URL_2')
    return Response(generate_frames(rtsp_url_2),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8099)
