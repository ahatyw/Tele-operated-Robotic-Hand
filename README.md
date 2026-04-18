 # Sci-Tech Labs: Tele-Operated Robotic Hand

**A clinical-grade, zero-latency dual robotic hand system controlled via wireless optical AI tracking.**

## 📌 Project Overview
The Sci-Tech Labs Labs  is our solution to bridging the gap between human biomechanics and robotic tele-operation. By using localized Wi-Fi networking and Google's MediaPipe neural network, this system tracks our hands in real-time—without any wearable sensors or data gloves—and mirrors those exact movements onto two physically distinct robotic hands. 

We designed this with clinical applications in mind. The software essentially acts as a "smart buffer" between the human operator and the robot, actively filtering out neurological tremors and ensuring a safe, locked grip when handling payloads.

## ✨ Key Biomedical & Software Features
* **Kinematic Tremor Filter:** We built an Exponential Moving Average (EMA) algorithm that mathematically erases human hand-shake or intention tremors in real-time. It ensures that the robotic servos only receive buttery-smooth, intentional data.
* **Pinch-Lock Safety Override:** The AI continuously measures the distance between the operator's thumb and index fingertips. If it detects a pinch, it safely overrides the live tracking and locks the servos into a rigid, high-torque grip so the robot doesn't drop what it's holding.
* **The "Spacebar Reveal" (Hot-Swappable Vision):** The system runs on a dynamic state machine. I can start the system tethered using a local laptop webcam, and with a single press of the spacebar, instantly hot-swap the vision feed to an untethered, cross-room Android IP Webcam without interrupting the robotic tracking.
* **Asymmetric String Calibration:** The AI natively handles two completely different physical kinematic systems at the same time:
  * **Left Hand:** Active Dual-String InMoov mechanism (Full 0°–180° mapping).
  * **Right Hand:** Passive Single-String Elastic mechanism (Compressed 20°–150° mapping to prevent tendon slack).

## 🏗️ Hardware Architecture
To guarantee zero-lag performance and completely eliminate 
  * The microcontroller logic is powered safely via USB, utilizing a unified common ground to the UBEC rails to prevent high-amperage motor noise from crashing the AI network.

## 🚀 How It Works (The Data Pipeline)
1. **See:** The Android IP Webcam captures the operator's hands and streams the video to the Mac.
2. **Think:** The Python script maps 42 independent 3D skeletal landmarks onto the hands, calculating the exact bend of every single finger.
3. **Filter:** The software applies the Tremor Filter, checks for Pinch-Lock overrides, and formats the data for the specific string mechanics of the Left vs. Right hand.
4. **Transmit:** The Mac fires a UDP network packet over Wi-Fi to the ESP32.
5. **Act:** The ESP32 receives the packet and instantly physically moves all 10 servos. 
*(This entire pipeline executes in milliseconds).*

---
*Designed and Engineered by Aniket, Pragati, Manas| Sci-Tech Labs*
