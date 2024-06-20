from flask import Flask, Response, render_template_string
import cv2
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
        <img src="/api/hassio_ingress/video_feed_1" width="640" height="480">
        <img src="/api/hassio_ingress/video_feed_2" width="640" height="480">
        <!-- Puedes añadir más streams aquí -->
    </div>
</body>
</html>
"""

def get_rtsp_url(cam_id):
    # Puedes definir múltiples URLs RTSP aquí
    rtsp_urls = {
        "1": os.getenv('RTSP_URL_1'),
        "2": os.getenv('RTSP_URL_2')
    }
    return rtsp_urls.get(cam_id)

def generate_frames(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise ValueError("Error: No se puede abrir la transmisión RTSP.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/video_feed_<cam_id>')
def video_feed(cam_id):
    rtsp_url = get_rtsp_url(cam_id)
    return Response(generate_frames(rtsp_url),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8099)
