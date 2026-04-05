/*
 * PROJECT: Wireless Robotic Hand (ESP32 + MediaPipe)
 * HARDWARE: ESP32 Dev Module + 5x Tower Pro 9g Servos
 * CONNECTION: UDP over Wi-Fi (Real-time)
 * POWER: Laptop USB (Caution: Move fingers smoothly to avoid power spikes)
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// ==========================================
// 1. WI-FI CREDENTIALS (EDIT THIS!)
// ==========================================
const char* WIFI_SSID = "M08ESP";      // Put your Wi-Fi Name here
const char* WIFI_PASS = "12345678";  // Put your Wi-Fi Password here

// ==========================================
// 2. PIN DEFINITIONS & SETTINGS
// ==========================================
// Servo GPIO Mapping
static const int PIN_THUMB  = 13;
static const int PIN_INDEX  = 14;
static const int PIN_MIDDLE = 25;
static const int PIN_RING   = 26;
static const int PIN_PINKY  = 27;

// UDP Port (Must match Python)
WiFiUDP udp;
const uint16_t UDP_PORT = 4210;

// Servo Objects
Servo sThumb, sIndex, sMiddle, sRing, sPinky;

// Packet Buffer
char packetBuf[255];

// ==========================================
// 3. CALIBRATION & INVERSION
// ==========================================
// Tower Pro 9g Pulse Widths (Standard)
static const int MIN_US = 544;
static const int MAX_US = 2400;

// DIRECTION CONTROL:
// If a finger moves backward (closes when you open), change 'false' to 'true'
bool INV_THUMB  = false;
bool INV_INDEX  = false;
bool INV_MIDDLE = false;
bool INV_RING   = false;
bool INV_PINKY  = false;

// Helper to constrain angles 0-180
int cleanAngle(int val, bool invert) {
  val = constrain(val, 0, 180);
  if (invert) return 180 - val;
  return val;
}

void setup() {
  Serial.begin(115200);
  delay(500);

  // 1. Attach Servos
  sThumb.attach(PIN_THUMB, MIN_US, MAX_US);
  sIndex.attach(PIN_INDEX, MIN_US, MAX_US);
  sMiddle.attach(PIN_MIDDLE, MIN_US, MAX_US);
  sRing.attach(PIN_RING, MIN_US, MAX_US);
  sPinky.attach(PIN_PINKY, MIN_US, MAX_US);

  // 2. Initialize to 0 degrees (Open Hand) immediately
  sThumb.write(cleanAngle(0, INV_THUMB));
  sIndex.write(cleanAngle(0, INV_INDEX));
  sMiddle.write(cleanAngle(0, INV_MIDDLE));
  sRing.write(cleanAngle(0, INV_RING));
  sPinky.write(cleanAngle(0, INV_PINKY));

  Serial.println("Servos Initialized to 0 deg.");

  // 3. Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("SUCCESS! ESP32 IP Address: ");
  Serial.println(WiFi.localIP()); // <--- COPY THIS IP FOR PYTHON

  // 4. Start UDP
  udp.begin(UDP_PORT);
  Serial.println("UDP Listener Started on Port 4210");
}

void loop() {
  // Check for incoming UDP packets
  int packetSize = udp.parsePacket();
  
  if (packetSize > 0) {
    int len = udp.read(packetBuf, 255);
    if (len > 0) packetBuf[len] = '\0'; // Null-terminate string

    // Parse values: "T,I,M,R,P"
    int t, i, m, r, p;
    // We expect 5 integers separated by commas
    if (sscanf(packetBuf, "%d,%d,%d,%d,%d", &t, &i, &m, &r, &p) == 5) {
      
      // Write to Servos
      sThumb.write(cleanAngle(t, INV_THUMB));
      sIndex.write(cleanAngle(i, INV_INDEX));
      sMiddle.write(cleanAngle(m, INV_MIDDLE));
      sRing.write(cleanAngle(r, INV_RING));
      sPinky.write(cleanAngle(p, INV_PINKY));
      
      // Debug print (optional, can slow down loop if too fast)
      // Serial.printf("T:%d I:%d M:%d R:%d P:%d\n", t, i, m, r, p);
    }
  }
}