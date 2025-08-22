from flask import Flask, request, jsonify, render_template
from datetime import datetime
from collections import defaultdict
import requests

app = Flask(__name__)

registered_devices = []

# Health check endpoint
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "server is running"}), 200

# Registration endpoint for Pi nodes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    registered_devices.append(data)
    # Just log the payload for now
    print(f"📥 Registered device: {data}")
    return jsonify({"message": "Registered"}), 200

@app.route("/api/motion", methods=["POST"])
def motion():
    data = request.json

    device_id = data.get("device_id")
    gpio = data.get("gpio")
    timestamp = data.get("timestamp", datetime.now().isoformat())

    if not device_id or gpio is None:
        return jsonify({"error": "Missing device_id or gpio"}), 400

    print(f"🚨 Motion detected from {device_id} on GPIO {gpio} at {timestamp}")

    # Optionally: log, trigger a scare, or notify admin here

    return jsonify({"status": "received"}), 200

@app.route("/dashboard")
def dashboard():
    # Map: device_id -> list of sounds
    sound_map = {}

    for device in registered_devices:
        device_id = device["device_id"]
        sound_map[device_id] = device.get("sounds", [])

    return render_template("dashboard.html", devices=registered_devices, sound_map=sound_map)


@app.route("/api/play", methods=["POST"])
def play_sound():
    device_id = request.form.get("device_id", "").lower()
    sound_file = request.form.get("sound_file")

    print(f"🔍 Looking for device: {device_id}")
    print("🧾 Registered devices:", [d["device_id"] for d in registered_devices])

    device = next((d for d in registered_devices if d["device_id"].lower() == device_id), None)
    if not device:
        return "Device not found", 404

    target_url = f"http://{device['ip']}:5001/api/play"  # 5001 is your client port
    try:
        res = requests.post(target_url, json={"sound_file": sound_file}, timeout=2)
        if res.status_code == 200:
            return f"Sent to {device_id}", 200
        else:
            return f"Device error: {res.status_code}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500



@app.route("/api/commands/<device_id>")
def get_commands(device_id):
    cmds = pending_commands.get(device_id, [])
    pending_commands[device_id] = []  # Clear after sending
    return jsonify({"commands": cmds})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
