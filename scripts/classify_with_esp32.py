#!/usr/bin/env python3
"""
FussyBin classifier using ESP32 camera over USB serial.
Make sure PyCharm's MicroPython REPL is disconnected before running.
"""
import sys
import pathlib
import time
import base64

import serial
import cv2
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.rubbish_item_classifier import classify_frame

SERIAL_PORT = "/dev/cu.usbserial-1130"
BAUD_RATE   = 115200

def fetch_frame(ser: serial.Serial) -> np.ndarray | None:
    ser.write(b"CAPTURE\n")
    n = int(ser.readline().decode().strip())
    b64 = ser.read(n)
    jpg = base64.b64decode(b64)
    return cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

print(f"Connecting to ESP32 on {SERIAL_PORT}...")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)

# Wait for READY signal from board
while True:
    line = ser.readline().decode(errors="ignore").strip()
    if line == "READY":
        print("ESP32 camera ready. Press SPACE to classify, Q to quit.\n")
        break
    print("ESP32:", line)

while True:
    frame = fetch_frame(ser)
    if frame is None:
        print("No frame received, retrying...")
        time.sleep(0.2)
        continue

    display = frame.copy()
    cv2.putText(display, "SPACE: classify  |  Q: quit",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("FussyBin", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    elif key == ord(' '):
        start = time.perf_counter()
        item, bin_, confidence = classify_frame(frame)
        elapsed = time.perf_counter() - start
        print(f"\n  Item  : {item}")
        print(f"  Bin   : {bin_}")
        print(f"  Score : {confidence:.3f}")
        print(f"  Time  : {elapsed:.3f}s")

        result_frame = frame.copy()
        colour = {
            "Recycling":     (0, 200, 255),
            "General Waste": (0,   0, 220),
            "Green Bin":     (0, 180,   0),
        }.get(bin_, (255, 255, 255))

        cv2.putText(result_frame, item,
                    (10,  60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colour, 2)
        cv2.putText(result_frame, f"-> {bin_}",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, colour, 3)
        cv2.putText(result_frame, f"confidence: {confidence:.2f}",
                    (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("FussyBin", result_frame)
        cv2.waitKey(2000)

ser.close()
cv2.destroyAllWindows()
