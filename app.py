import os
import json
import cv2
import qrcode
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash

app = Flask(__name__)
app.secret_key = "your_secret_key"
DATA_FILE = "qr_data_store.json"
QR_OUTPUT_DIR = "static"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def scan_qr_from_image(image_path):
    img = cv2.imread(image_path)
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img)
    if data:
        return data
    else:
        raise ValueError("No QR code found in image.")

def regenerate_qr(name, data_string):
    output_path = os.path.join(QR_OUTPUT_DIR, f"{name}.png")
    qr = qrcode.make(data_string)
    qr.save(output_path)
    return output_path

@app.route('/', methods=['GET', 'POST'])
def index():
    data = load_data()
    if request.method == 'POST':
        file = request.files.get('file')
        name = request.form.get('name')

        if not file or not name:
            flash("Device name and image file are required.", "error")
            return redirect(url_for('index'))

        image_path = os.path.join("temp_upload.png")
        file.save(image_path)

        try:
            qr_string = scan_qr_from_image(image_path)
            data[name] = qr_string
            save_data(data)
            regenerate_qr(name, qr_string)
            flash(f"Stored and generated QR for '{name}'", "success")
        except Exception as e:
            flash(str(e), "error")
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)
        return redirect(url_for('index'))

    return render_template("index.html", devices=data)

@app.route('/qr/<name>')
def get_qr(name):
    return send_from_directory(QR_OUTPUT_DIR, f"{name}.png")

if __name__ == '__main__':
    os.makedirs(QR_OUTPUT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5050, debug=True)

