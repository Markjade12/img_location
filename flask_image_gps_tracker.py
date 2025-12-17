# ======================= app.py =======================
from flask import Flask, request, render_template
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import base64
from io import BytesIO

app = Flask(__name__)

# ---------- EXIF FUNCTIONS ----------

def get_exif(img):
    exif_data = img._getexif()
    if not exif_data:
        return None
    exif = {}
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        exif[decoded] = value
    return exif


def get_gps_info(exif):
    if 'GPSInfo' not in exif:
        return None
    gps_info = {}
    for key in exif['GPSInfo'].keys():
        decode = GPSTAGS.get(key, key)
        gps_info[decode] = exif['GPSInfo'][key]
    return gps_info


def convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def get_coordinates(gps_info):
    try:
        lat = convert_to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef'] != 'N':
            lat = -lat
        lon = convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef'] != 'E':
            lon = -lon
        return lat, lon
    except Exception:
        return None, None

# ---------- ROUTE ----------

@app.route('/', methods=['GET', 'POST'])
def index():
    lat = lon = error = None

    if request.method == 'POST':
        # Image upload
        if 'image' in request.files and request.files['image'].filename != '':
            img = Image.open(request.files['image'])
        # Camera capture (base64)
        elif 'camera_image' in request.form:
            data = request.form['camera_image'].split(',')[1]
            img = Image.open(BytesIO(base64.b64decode(data)))
        else:
            return render_template('index.html', error='No image received')

        exif = get_exif(img)
        if exif:
            gps_info = get_gps_info(exif)
            if gps_info:
                lat, lon = get_coordinates(gps_info)
                if not lat or not lon:
                    error = 'GPS exists but cannot be parsed'
            else:
                error = 'No GPS data found'
        else:
            error = 'No EXIF metadata found'

    return render_template('index.html', lat=lat, lon=lon, error=error)


if __name__ == '__main__':
    app.run(debug=True)


# ======================= templates/index.html =======================
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Image & Camera GPS Tracker</title>
<style>
body { font-family: Arial; background:#f5f5f7; padding:30px }
.box { background:white; padding:20px; max-width:700px; margin:auto; border-radius:14px }
video { width:100%; border-radius:12px }
button { background:#007aff; color:white; border:none; padding:10px 20px; border-radius:8px }
iframe { width:100%; height:350px; border:0; border-radius:12px }
</style>
</head>
<body>
<div class="box">
<h2>📍 Upload or Capture Image</h2>

<!-- Upload Image -->
<form method="POST" enctype="multipart/form-data">
<input type="file" name="image" accept="image/*">
<br><br>
<button type="submit">Upload Image</button>
</form>

<hr>

<!-- Camera Capture -->
<video id="video" autoplay></video><br><br>
<button onclick="capture()">Capture Camera</button>

<form method="POST">
<input type="hidden" name="camera_image" id="camera_image">
<br>
<button type="submit">Send Capture</button>
</form>

{% if error %}
<p style="color:red">{{ error }}</p>
{% endif %}

{% if lat and lon %}
<h3>📍 Location Found</h3>
<p>Latitude: {{ lat }}</p>
<p>Longitude: {{ lon }}</p>
<iframe src="https://www.google.com/maps?q={{ lat }},{{ lon }}&output=embed"></iframe>
{% endif %}
</div>

<script>
navigator.mediaDevices.getUserMedia({ video: true })
.then(stream => document.getElementById('video').srcObject = stream)
.catch(err => console.error(err));

function capture() {
    const video = document.getElementById('video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    document.getElementById('camera_image').value = canvas.toDataURL('image/jpeg');
}
</script>
</body>
</html>
