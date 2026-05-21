#!/usr/bin/env python3
"""
FussyBin classifier using ESP32 camera over USB serial.
Make sure PyCharm's MicroPython REPL is disconnected before running.
"""
import sys
import pathlib
import time
import base64
import os
from dotenv import load_dotenv

import serial
import cv2
import numpy as np

load_dotenv()

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.rubbish_item_classifier import classify_frame
from src.display import draw_prompt, draw_classification

SERIAL_PORT = os.environ.get("FUSSYBIN_SERIAL_PORT", "/dev/cu.usbserial-1130")
BAUD_RATE   = int(os.environ.get("FUSSYBIN_BAUD_RATE", "115200"))

def fetch_frame(ser: serial.Serial) -> np.ndarray | None:
    """Request and decode a single JPEG frame from the ESP32 over serial.

    Returns None on any malformed response (length parse error, ESP32 ERROR
    reply, short read) so the caller can retry without crashing.
    """
    ser.write(b"CAPTURE\n")
    line = ser.readline().decode(errors="ignore").strip()
    if not line or line == "ERROR":
        return None
    try:
        n = int(line)
    except ValueError:
        return None

    buf = bytearray()
    while len(buf) < n:
        chunk = ser.read(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)

    try:
        jpg = base64.b64decode(bytes(buf))
    except (ValueError, base64.binascii.Error):
        return None
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

    cv2.imshow("FussyBin", draw_prompt(frame))

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

        cv2.imshow("FussyBin", draw_classification(frame, item, bin_, confidence))
        cv2.waitKey(2000)

ser.close()
cv2.destroyAllWindows()
