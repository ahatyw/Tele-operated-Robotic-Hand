import cv2
import mediapipe as mp
import socket
import math
import time

# ==========================================
# 🔴 EDIT THESE TWO IP ADDRESSES
# ==========================================
IP_WEBCAM_URL = "http://10.165.49.66:8080/video" 
ESP32_MASTER_IP = "10.165.49.58" # The single IP from the Arduino Serial Monitor                   

PORT = 1111

# ==========================================
# SYSTEM SETUP
# ==========================================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Store current angles globally so if a hand goes off-camera, it stays in its last known position
current_angles = {
    'Left': [90, 90, 90, 90, 90],
    'Right': [90, 90, 90, 90, 90]
}

def calculate_distance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def map_angle(distance, min_dist, max_dist, min_angle, max_angle):
    angle = min_angle + (distance - min_dist) * (max_angle - min_angle) / (max_dist - min_dist)
    return int(max(min(angle, max_angle), min_angle)) 

def apply_tremor_filter(current_angle, prev_angle, smoothing_factor=0.3):
    return int((current_angle * smoothing_factor) + (prev_angle * (1.0 - smoothing_factor)))

# ==========================================
# STATE MACHINE SETUP
# ==========================================
current_mode = "MAC_WEBCAM"
print("TechAni Labs Interface Booting...")
cap = cv2.VideoCapture(0) 

# ==========================================
# MAIN VIDEO LOOP
# ==========================================
while True:
    success, frame = cap.read()
    if not success:
        continue

    if current_mode == "MAC_WEBCAM":
        frame = cv2.flip(frame, 1)

    frame = cv2.resize(frame, (640, 480))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # We only send a packet if at least one hand is detected to save network bandwidth
    packet_needed = False

    if results.multi_hand_landmarks and results.multi_handedness:
        packet_needed = True
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            
            hand_label = handedness.classification[0].label 
            lm = hand_landmarks.landmark 
            
            # 1. PINCH-LOCK
            is_pinching = calculate_distance(lm[4], lm[8]) < 0.05 

            # 2. RAW ANGLES (0.1 to 0.4 distance mapping)
            raw_t = map_angle(calculate_distance(lm[0], lm[4]), 0.1, 0.4, 0, 180)
            raw_i = map_angle(calculate_distance(lm[0], lm[8]), 0.1, 0.4, 0, 180)
            raw_m = map_angle(calculate_distance(lm[0], lm[12]), 0.1, 0.4, 0, 180)
            raw_r = map_angle(calculate_distance(lm[0], lm[16]), 0.1, 0.4, 0, 180)
            raw_p = map_angle(calculate_distance(lm[0], lm[20]), 0.1, 0.4, 0, 180)

            if is_pinching: raw_t, raw_i = 180, 180 

            # 3. TREMOR FILTER & STATE SAVING
            prev = current_angles[hand_label]
            smooth_t = apply_tremor_filter(raw_t, prev[0])
            smooth_i = apply_tremor_filter(raw_i, prev[1])
            smooth_m = apply_tremor_filter(raw_m, prev[2])
            smooth_r = apply_tremor_filter(raw_r, prev[3])
            smooth_p = apply_tremor_filter(raw_p, prev[4])

            # 4. STRING CALIBRATION (Apply right before saving)
            if hand_label == "Right":
                smooth_t = map_angle(smooth_t, 0, 180, 20, 150)
                smooth_i = map_angle(smooth_i, 0, 180, 20, 150)
                smooth_m = map_angle(smooth_m, 0, 180, 20, 150)
                smooth_r = map_angle(smooth_r, 0, 180, 20, 150)
                smooth_p = map_angle(smooth_p, 0, 180, 20, 150)

            current_angles[hand_label] = [smooth_t, smooth_i, smooth_m, smooth_r, smooth_p]

            # UI Overlays
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            if is_pinching:
                cv2.putText(frame, f"{hand_label} PINCH LOCK", (10, 50 if hand_label == "Left" else 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    # 5. UNIFIED HARDWARE ROUTING
    if packet_needed:
        L = current_angles['Left']
        R = current_angles['Right']
        # Construct the massive 10-servo packet
        packet = f"<B,{L[0]},{L[1]},{L[2]},{L[3]},{L[4]},{R[0]},{R[1]},{R[2]},{R[3]},{R[4]}>"
        sock.sendto(packet.encode(), (ESP32_MASTER_IP, PORT))

    cv2.putText(frame, f"MODE: {current_mode}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("TechAni Labs - Master Interface", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '): 
        if current_mode == "MAC_WEBCAM":
            current_mode = "IP_WEBCAM"
            cap.release() 
            cap = cv2.VideoCapture(IP_WEBCAM_URL) 
        else:
            current_mode = "MAC_WEBCAM"
            cap.release() 
            cap = cv2.VideoCapture(0) 

cap.release()
cv2.destroyAllWindows()