#include <SoftwareSerial.h>  //for bluetooth module communication

const int irPin1 = 2;       // First IR sensor pin (Left)
const int irPin2 = 3;       // Second IR sensor pin (Right)

// Motor control pins for L298N
const int ENA_PIN = 9;      // L298N Enable A pin (for PWM or simple ON/OFF)
const int IN1_PIN = 6;      // L298N Input 1 for Motor A
const int IN2_PIN = 7;      // L298N Input 2 for Motor A

const int buzzerPin = 8;    // Buzzer pin
const int BT_RX = 10;       // Bluetooth RX pin (connects to TX of HC-05)
const int BT_TX = 11;       // Bluetooth TX pin (connects to RX of HC-05)

// Variables to track state changes and timing
bool lastMotorState = true;  // true = motor running, false = motor stopped
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 1000;   // Send data every 1 second (1000 milliseconds)

// Flag to indicate if motor/buzzer is currently controlled by ML prediction from Python
bool ml_controlled = false; // manual/IR control is active

// Initialize SoftwareSerial for Bluetooth communication
SoftwareSerial bluetooth(BT_RX, BT_TX);

void setup() {
  Serial.begin(9600);      // For debugging via Arduino IDE Serial Monitor
  bluetooth.begin(9600);  // For communication with HC-05 Bluetooth module

  pinMode(irPin1, INPUT);
  pinMode(irPin2, INPUT);

  // Motor Driver Pins
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  pinMode(buzzerPin, OUTPUT);

  // Initial state: Motor ON, Buzzer OFF (assuming motor runs forward by default)
  digitalWrite(ENA_PIN, HIGH); // Enable motor
  digitalWrite(IN1_PIN, HIGH); // Set direction (forward)
  digitalWrite(IN2_PIN, LOW);
  digitalWrite(buzzerPin, LOW);

  Serial.println("System Started - Ready for operation.");
  bluetooth.println("System Started - Ready for operation.");
}

void setMotorDirection(bool forward) {
    if (forward) {
        digitalWrite(IN1_PIN, HIGH);
        digitalWrite(IN2_PIN, LOW);
    } else { // Backward (if needed) - or just stop for your current logic
        digitalWrite(IN1_PIN, LOW);
        digitalWrite(IN2_PIN, HIGH); // Or LOW for both to stop
    }
}

void loop() {
  if (!ml_controlled) {
    int irValue1 = digitalRead(irPin1); // Read Left Sensor
    int irValue2 = digitalRead(irPin2); // Read Right IR sensor

    bool objectDetected = (irValue1 == LOW || irValue2 == LOW); // True if any object is detected
    bool motorShouldRun = !objectDetected;

    if (motorShouldRun) {
        digitalWrite(ENA_PIN, HIGH); // Enable motor
        setMotorDirection(true);     // Set to run forward
        digitalWrite(buzzerPin, LOW);
    } else {
        digitalWrite(ENA_PIN, LOW);  // Disable motor
        setMotorDirection(false);    // Ensure motor inputs are low for stop
        digitalWrite(buzzerPin, HIGH);
    }
  }

  unsigned long currentTime = millis();
  bool currentMotorIsRunning = digitalRead(ENA_PIN); // Assuming ENA_PIN controls overall motor state

  // Send structured log if SEND_INTERVAL has passed
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    int irValue1 = digitalRead(irPin1);
    int irValue2 = digitalRead(irPin2);

    String logMsg = "LOG,";
    logMsg += String(currentTime) + ",";
    logMsg += "L:" + String(irValue1) + ",";
    logMsg += "R:" + String(irValue2);

    Serial.println(logMsg);
    bluetooth.println(logMsg);

    //reset
    lastMotorState = currentMotorIsRunning;
    lastSendTime = currentTime;
  }

  //Check for incoming Bluetooth commands from Python
  if (bluetooth.available()) {
    char cmd = bluetooth.read();
    handleCommand(cmd);
  }

  delay(50);
}

void handleCommand(char command) {
  switch (command) {
    case '1': // Manual: Motor ON
      ml_controlled = false;
      digitalWrite(ENA_PIN, HIGH);
      setMotorDirection(true); // Run forward
      digitalWrite(buzzerPin, LOW);
      bluetooth.println("Manual: Motor ON (ML disabled)");
      Serial.println("Manual: Motor ON (ML disabled)");
      lastMotorState = true;
      lastSendTime = millis();
      break;

    case '0': // Manual: Motor OFF
      ml_controlled = false;
      digitalWrite(ENA_PIN, LOW); // Stop motor
      setMotorDirection(false); 
      digitalWrite(buzzerPin, HIGH);
      bluetooth.println("Manual: Motor OFF (ML disabled)");
      Serial.println("Manual: Motor OFF (ML disabled)");
      lastMotorState = false;
      lastSendTime = millis();
      break;

    case 's':
    case 'S':
      sendStatus();
      break;

    case 'D': // ML: Drowsy detected - Stop motor, Buzzer ON
      ml_controlled = true;
      digitalWrite(ENA_PIN, LOW); // Stop motor
      setMotorDirection(false); // Ensure motor inputs are low for stop
      digitalWrite(buzzerPin, HIGH);
      bluetooth.println("ML_Action: Drowsy detected! Motor stopped, Buzzer ON.");
      Serial.println("ML_Action: Drowsy detected! Motor stopped, Buzzer ON.");
      lastMotorState = false;
      lastSendTime = millis();
      break;

    case 'A': // ML: Alert - Motor ON, Buzzer OFF
      ml_controlled = true;
      digitalWrite(ENA_PIN, HIGH);
      setMotorDirection(true); // Run forward
      digitalWrite(buzzerPin, LOW);
      bluetooth.println("ML_Action: Alert! Motor running, Buzzer OFF.");
      Serial.println("ML_Action: Alert! Motor running, Buzzer OFF.");
      lastMotorState = true;
      lastSendTime = millis();
      break;

    default:
      bluetooth.println("Unknown command");
      Serial.println("Unknown command received");
  }
}

void sendStatus() {
  int irValue1 = digitalRead(irPin1);
  int irValue2 = digitalRead(irPin2);

  // For motor status we now check ENA_PIN. If it's HIGH, the motor is enabled.
  String statusLogMsg = "STATUS_REPORT,";
  statusLogMsg += String(millis()) + ",";
  statusLogMsg += "L:" + String(irValue1) + ",";
  statusLogMsg += "R:" + String(irValue2) + ",";
  statusLogMsg += String(digitalRead(ENA_PIN) ? 1 : 0) + ","; // Motor status
  statusLogMsg += String(digitalRead(buzzerPin) ? 1 : 0); // Buzzer status

  bluetooth.println(statusLogMsg);
  Serial.println(statusLogMsg);
}