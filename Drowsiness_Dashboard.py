import serial
import time
import re
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from flask import Flask, jsonify, render_template_string 
import threading 
import logging
import csv

# --- Configuration ---
bluetooth_port = 'COM5'
baud_rate = 9600
flask_port = 5000
flask_host_ip = '0.0.0.0'
DATA_LOG_FILE = 'expo_analysis_data.csv'
CONFIRMATION_DELAY = 5.0  # Seconds eyes must be closed before alert

# Disable default Flask logging
log = logging.getLogger('werkzeug') 
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Global data containers
current_data = {
    "timestamp": 0, "ir1_value": 1, "ir2_value": 1,
    "motor_state": 1, "buzzer_state": 0,
    "drowsiness_prediction": "NOT DROWSY",
    "message": "System initializing...",
    "graph_labels": [], "graph_values": [] # For real-time analytics
}

history_limit = 20  # How many points to show on the graph
log_count = 0  # Counter for the first 100 readings

# Regular Expressions
log_pattern = re.compile(r"^LOG,(\d+),L:(\d+),R:(\d+)$")

### Machine Learning Model Setup
model_filename = 'drowsiness_rf_model.pkl'
try:
    drowsiness_model = joblib.load(model_filename)
except:
    X_dummy = np.array([[1, 1], [1, 0], [0, 1], [0, 0]])
    y_dummy = np.array([0, 1, 1, 1])
    drowsiness_model = RandomForestClassifier(n_estimators=10, random_state=42)
    drowsiness_model.fit(X_dummy, y_dummy)

def send_command(ser_connection, command_char):
    if ser_connection and ser_connection.is_open:
        ser_connection.write(command_char.encode('utf-8'))

# New HTML with Live Graphing (Chart.js)
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Drowsiness Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }
        h1 { color: #1a73e8; text-align: center; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .stat { border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center; }
        .val { font-size: 24px; font-weight: bold; color: #1a73e8; }
        .prediction-box { font-size: 2em; text-align: center; padding: 20px; border-radius: 10px; margin: 20px 0; font-weight: bold; }
        .alert { background: #fee; color: #c00; border: 2px solid #c00; }
        .safe { background: #efe; color: #080; border: 2px solid #080; }
        canvas { width: 100% !important; height: 300px !important; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Driver Health & Safety Analytics</h1>
        <div id="pred_box" class="prediction-box safe">NOT DROWSY</div>
        <div class="grid">
            <div class="stat">IR1: <span class="val" id="ir1">N/A</span></div>
            <div class="stat">IR2: <span class="val" id="ir2">N/A</span></div>
            <div class="stat">Car Status: <span class="val" id="motor">Running</span></div>
            <div class="stat">Buzzer: <span class="val" id="buzzer">Off</span></div>
        </div>
        <p style="text-align:center"><i>System Message: <span id="msg">...</span></i></p>
        <canvas id="liveChart"></canvas>
    </div>

    <script>
        const ctx = document.getElementById('liveChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Drowsiness State (1=Drowsy)', data: [], borderColor: '#1a73e8', tension: 0.3, fill: true, backgroundColor: 'rgba(26, 115, 232, 0.1)' }] },
            options: { scales: { y: { min: 0, max: 1, ticks: { stepSize: 1 } } } }
        });

        function update() {
            fetch('/get_data').then(r => r.json()).then(data => {
                document.getElementById('ir1').innerText = data.ir1_value;
                document.getElementById('ir2').innerText = data.ir2_value;
                document.getElementById('motor').innerText = data.motor_state ? "Running" : "STOPPED";
                document.getElementById('buzzer').innerText = data.buzzer_state ? "ON" : "OFF";
                document.getElementById('msg').innerText = data.message;
                
                const box = document.getElementById('pred_box');
                box.innerText = data.drowsiness_prediction;
                box.className = data.drowsiness_prediction.includes("DROWSY") ? "prediction-box alert" : "prediction-box safe";

                chart.data.labels = data.graph_labels;
                chart.data.datasets[0].data = data.graph_values;
                chart.update('none');
            });
        }
        setInterval(update, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_DASHBOARD)

@app.route('/get_data')
def get_sensor_data(): return jsonify(current_data)

def serial_communication_thread():
    global current_data, log_count
    ser = None
    drowsy_start_time = None
    alert_active = False

    # Initialize CSV file with headers
    with open(DATA_LOG_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'IR1', 'IR2', 'Prediction'])

    try:
        ser = serial.Serial(bluetooth_port, baud_rate, timeout=1)
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                match = log_pattern.match(line)
                
                if match:
                    ts, ir1, ir2 = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    pred = int(drowsiness_model.predict([[ir1, ir2]])[0])
                    
                    # 1. Delayed Detection Logic (5 Seconds)
                    if pred == 1:
                        if drowsy_start_time is None: drowsy_start_time = time.time()
                        elapsed = time.time() - drowsy_start_time
                        
                        if elapsed >= CONFIRMATION_DELAY:
                            if not alert_active:
                                send_command(ser, 'D')
                                alert_active = True
                            current_data["drowsiness_prediction"] = "DROWSY (CONFIRMED)"
                        else:
                            current_data["message"] = f"Confirming drowsiness... {int(elapsed)}s"
                            current_data["drowsiness_prediction"] = "PENDING..."
                    else:
                        drowsy_start_time = None
                        if alert_active:
                            send_command(ser, 'A')
                            alert_active = False
                        current_data["drowsiness_prediction"] = "NOT DROWSY"
                        current_data["message"] = "Driver active."

                    # 2. Update Graph Data
                    current_data["graph_labels"].append(time.strftime('%H:%M:%S'))
                    current_data["graph_values"].append(pred)
                    if len(current_data["graph_labels"]) > history_limit:
                        current_data["graph_labels"].pop(0)
                        current_data["graph_values"].pop(0)

                    # 3. Save first 100 readings to file
                    if log_count < 100:
                        with open(DATA_LOG_FILE, mode='a', newline='') as f:
                            csv.writer(f).writerow([ts, ir1, ir2, pred])
                        log_count += 1

                    current_data.update({"ir1_value": ir1, "ir2_value": ir2, 
                                         "motor_state": 0 if alert_active else 1, 
                                         "buzzer_state": 1 if alert_active else 0})
            time.sleep(0.1)
    except Exception as e: print(f"Serial Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=serial_communication_thread, daemon=True).start()
    
    # Start the Flask web server in the main thread
    print(f"\nFlask web dashboard accessible at: http://ipaddress:{flask_port}/")
    print("------------------------------------------------------------------")
    
    app.run(host=flask_host_ip, port=flask_port, debug=False)