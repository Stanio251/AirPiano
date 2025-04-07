import cv2
import mediapipe as mp
import time
import math
from collections import deque
from midi_sound import play
import threading

# Finger names and landmark indexes
finger_ids = {
    'Thumb': 4,
    'Index': 8,
    'Middle': 12,
    'Ring': 16,
    'Pinky': 20
}

notes = [60, 62, 64, 65, 67]

# Initialize tracking data per finger
tracking_data = {
    name: {
        'prev_x': None,
        'prev_y': None,
        'prev_speed': 0.0,
        'prev_time': time.time(),
        'speed_buffer': deque(maxlen=3),
        'recent_raw_speeds': deque(maxlen=5),
        'note': note  # Here we assign the note
    }
    for name, note in zip(finger_ids, notes)
}

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 280)

def detect_finger_tap(finger_name, x, y, data):
    curr_time = time.time()
    dt = curr_time - data['prev_time']
    data['prev_time'] = curr_time

    if data['prev_x'] is not None and data['prev_y'] is not None and dt > 0:
        dx = x - data['prev_x']
        dy = y - data['prev_y']
        distance = math.hypot(dx, dy)

        # Calculate raw speed
        raw_speed = distance / dt
        data['recent_raw_speeds'].append(raw_speed)

        # Add to buffer
        data['speed_buffer'].append(raw_speed)

        # Compute moving average
        smoothed_speed = sum(data['speed_buffer']) / len(data['speed_buffer'])
        
        # Calculate acceleration using smoothed speed
        acceleration = (raw_speed - data['prev_speed']) / dt
        # TAP DETECTION
        tap_detected = False
        was_fast_recently = any(s > 200 for s in data['recent_raw_speeds'])
        if smoothed_speed < 50 and acceleration < -800 and was_fast_recently:
            tap_detected = True
            print(f"🎵 {finger_name} TAP detected!")
            threading.Thread(target=play, args=(data['note'], 60), daemon=True).start()

        data['prev_speed'] = smoothed_speed

    data['prev_x'], data['prev_y'] = x, y


# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            h, w, _ = frame.shape
            for finger_name, landmark_id in finger_ids.items():
                x = int(hand_landmarks.landmark[landmark_id].x * w)
                y = int(hand_landmarks.landmark[landmark_id].y * h)
                detect_finger_tap(finger_name, x, y, tracking_data[finger_name])

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Hand Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
