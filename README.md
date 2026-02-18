🚗 Project: AI Driver Drowsiness Detection System

In this project, I developed an AI + IoT based real-time Driver Drowsiness Detection System that monitors a driver's eye state using IR sensors, predicts fatigue using a Machine Learning model, and automatically triggers safety actions like buzzer alert and motor stop.

The system also includes a Live Web Dashboard for real-time monitoring and analytics.

Key Technical Steps
Hardware Data Collection

IR eye-blink sensors detect whether the driver’s eyes are:

Open (1)

Closed (0)

Data is sent in real-time through Bluetooth communication.

Serial Communication

Python reads live sensor values from the microcontroller via Bluetooth Serial Port.

Machine Learning Prediction

A Random Forest Classifier predicts driver state:

0 → Not Drowsy

1 → Drowsy

False Alarm Filtering

The system confirms drowsiness only after 5 seconds continuous eye closure, reducing incorrect alerts.

Safety Automation

When drowsiness is confirmed:

🚨 Buzzer turns ON

🛑 Motor turns OFF (vehicle simulation)

Live Dashboard

A Flask-based web dashboard displays real-time:

Driver status

Sensor values

Prediction results

Motor & buzzer state

Live graph visualization

Data Logging

First 100 readings are saved into a .csv file for analysis and performance testing.

❓ Why Do We Use a Drowsiness Detection System?

Driver fatigue is one of the leading causes of road accidents worldwide. This intelligent system helps prevent accidents using real-time monitoring and AI prediction.

1. Prevents Accidents

Drowsy drivers have slow reaction time and may fall asleep unknowingly. The system detects fatigue early and alerts the driver immediately.

2. Real-Time Monitoring

Unlike traditional alarms, this system continuously monitors eye state and predicts fatigue using Machine Learning.

3. Reduces False Alerts

The 5-second confirmation logic ensures alerts are triggered only when real drowsiness occurs.

4. Automated Safety Response

When fatigue is detected:

Buzzer warns the driver

Motor automatically stops (simulated safety control)

5. Data Collection & Analysis

The system records sensor data for:

Performance evaluation

Accuracy testing

Research & documentation

⚙️ Technologies Used
Hardware

IR Eye Blink Sensors

Microcontroller (Arduino)

Bluetooth Module

Buzzer

Motor (Vehicle Simulation)

Software

Python

Flask (Web Server)

Scikit-Learn (Machine Learning)

Random Forest Algorithm

NumPy

Joblib

HTML / CSS / JavaScript

Chart.js (Live Graph)

🤖 How the System Works

IR sensors detect eye blink → send values to Python

Python loads trained Random Forest ML Model

Model predicts Drowsy / Not Drowsy

If eye closed continuously for 5 seconds → Confirmed Drowsy

System activates:

🚨 Buzzer ON

🛑 Motor OFF

Data displayed on Live Web Dashboard

First 100 readings saved into CSV

📊 Output File
expo_analysis_data.csv


Contains:

Sensor values

Prediction results

Timestamp data

Used for project analysis & evaluation.

🚀 How to Run My Project
1. Install Dependencies
pip install flask numpy scikit-learn joblib pyserial

2. Connect Hardware

Connect IR sensors & buzzer to microcontroller

Connect Bluetooth module

Update COM port in code:

bluetooth_port = 'COM5'

3. Run the Python Script
python Drowsiness_Dashboard.py

4. Open Live Dashboard
http://localhost:5000

🎯 Key Features

Real-time drowsiness detection

Machine learning prediction

False alarm filtering (5 sec confirmation)

Live web dashboard monitoring

Automatic motor stop

Buzzer alert system

Data logging for analysis

IoT + AI integration
