from flask import Flask, render_template_string
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
        <video width="640" height="480" controls>
            <source src="{{ rtsp_url_1 }}" type="application/x-rtsp">
            Your browser does not support the RTSP stream.
        </video>
        <video width="640" height="480" controls>
            <source src="{{ rtsp_url_2 }}" type="application/x-rtsp">
            Your browser does not support the RTSP stream.
        </video>
        <!-- Puedes añadir más streams aquí -->
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    rtsp_url_1 = os.getenv('RTSP_URL_1')
    rtsp_url_2 = os.getenv('RTSP_URL_2')
    return render_template_string(html_template, rtsp_url_1=rtsp_url_1, rtsp_url_2=rtsp_url_2)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8099)
