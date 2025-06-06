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
    """Load data from the JSON store and upgrade legacy formats."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

        # Legacy format was a flat mapping of name->qr_string
        if isinstance(data, dict) and 'devices' not in data:
            data = {
                'devices': {k: {'qr': v, 'category': '', 'room': ''} for k, v in data.items()},
                'categories': [],
                'rooms': []
            }
            save_data(data)
        return data

    return {'devices': {}, 'categories': [], 'rooms': []}

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
@app.route('/')
def index():
    data = load_data()
    sort_by = request.args.get('sort', 'room')
    devices = data.get('devices', {})
    if sort_by == 'category':
        sorted_devices = dict(
            sorted(devices.items(), key=lambda item: (item[1].get('category', ''), item[0]))
        )
    else:
        sorted_devices = dict(
            sorted(devices.items(), key=lambda item: (item[1].get('room', ''), item[0]))
        )
    return render_template('index.html', devices=sorted_devices, sort_by=sort_by)

@app.route('/add', methods=['GET', 'POST'])
def add_device():
    data = load_data()
    if request.method == 'POST':
        file = request.files.get('file')
        name = request.form.get('name')
        category = request.form.get('category', '')
        room = request.form.get('room', '')
        if not file or not name:
            flash('Device name and image file are required.', 'error')
            return redirect(url_for('add_device'))
        image_path = os.path.join('temp_upload.png')
        file.save(image_path)
        try:
            qr_string = scan_qr_from_image(image_path)
            data['devices'][name] = {
                'qr': qr_string,
                'category': category,
                'room': room,
            }
            save_data(data)
            regenerate_qr(name, qr_string)
            flash(f"Stored and generated QR for '{name}'", 'success')
        except Exception as e:
            flash(str(e), 'error')
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)
        return redirect(url_for('index'))
    return render_template('add_device.html', categories=data.get('categories', []), rooms=data.get('rooms', []))


@app.route('/qr/<name>')
def get_qr(name):
    return send_from_directory(QR_OUTPUT_DIR, f"{name}.png")


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Manage categories and rooms."""
    data = load_data()
    if request.method == 'POST':
        action = request.form.get('action')
        value = request.form.get('value', '').strip()
        if action == 'add_category' and value:
            if value not in data['categories']:
                data['categories'].append(value)
                save_data(data)
        elif action == 'delete_category':
            if value in data['categories']:
                data['categories'].remove(value)
                for dev in data['devices'].values():
                    if dev.get('category') == value:
                        dev['category'] = ''
                save_data(data)
        elif action == 'add_room' and value:
            if value not in data['rooms']:
                data['rooms'].append(value)
                save_data(data)
        elif action == 'delete_room':
            if value in data['rooms']:
                data['rooms'].remove(value)
                for dev in data['devices'].values():
                    if dev.get('room') == value:
                        dev['room'] = ''
                save_data(data)
        return redirect(url_for('settings'))

    return render_template(
        'settings.html',
        categories=data.get('categories', []),
        rooms=data.get('rooms', [])
    )


@app.route('/edit_device/<name>', methods=['GET', 'POST'])
def edit_device(name):
    data = load_data()
    device = data['devices'].get(name)
    if not device:
        flash('Device not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_name = request.form.get('name').strip()
        category = request.form.get('category', '')
        room = request.form.get('room', '')

        if not new_name:
            flash('Device name is required.', 'error')
            return redirect(url_for('edit_device', name=name))

        if new_name != name and new_name in data['devices']:
            flash('A device with that name already exists.', 'error')
            return redirect(url_for('edit_device', name=name))

        # rename key if necessary
        if new_name != name:
            data['devices'][new_name] = device
            del data['devices'][name]
            old_path = os.path.join(QR_OUTPUT_DIR, f"{name}.png")
            new_path = os.path.join(QR_OUTPUT_DIR, f"{new_name}.png")
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            name = new_name
            device = data['devices'][new_name]

        device['category'] = category
        device['room'] = room

        save_data(data)
        flash('Device updated.', 'success')
        return redirect(url_for('index'))

    return render_template(
        'edit_device.html',
        name=name,
        device=device,
        categories=data.get('categories', []),
        rooms=data.get('rooms', [])
    )

if __name__ == '__main__':
    os.makedirs(QR_OUTPUT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5050)

