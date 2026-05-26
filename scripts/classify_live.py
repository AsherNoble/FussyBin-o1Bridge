#!/usr/bin/env python3
"""
Live webcam classification with ESP32 bin control.
"""
import os
import sys
import pathlib
import time
import subprocess
from dotenv import load_dotenv

import serial
import cv2

load_dotenv()

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.rubbish_item_classifier import classify_frame
from src.display import draw_prompt, draw_classification

KNOWN_SERIAL_PORTS = [
    "/dev/cu.usbserial-110",
    "/dev/cu.usbserial-130",
    "/dev/cu.usbserial-1130",
    "/dev/cu.usbserial-1140",
]


def resolve_serial_port() -> str:
    env_port = os.environ.get("FUSSYBIN_SERIAL_PORT")
    if env_port:
        return env_port

    for port in KNOWN_SERIAL_PORTS:
        if pathlib.Path(port).exists():
            return port

    ports = ", ".join(KNOWN_SERIAL_PORTS)
    print(f"ERROR: no ESP32 serial port found. Tried: {ports}")
    sys.exit(1)


SERIAL_PORT = resolve_serial_port()
BAUD_RATE = int(os.environ.get("FUSSYBIN_BAUD_RATE", "115200"))
COOLDOWN_SECONDS = 4.0
FRAME_DELAY_MS = 200
BIN_TO_COMMAND = {"Recycling": "B", "General Waste": "R", "Green Bin": "G"}

print(f"Connecting to ESP32 on {SERIAL_PORT}...")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)

while True:
    line = ser.readline().decode(errors="ignore").strip()
    if line == "READY":
        break
    if line:
        print(f"ESP32: {line}")

esp32_ip = ser.readline().decode(errors="ignore").strip()
print(f"ESP32 IP: {esp32_ip}")
ser.reset_input_buffer()

stream_url = f"http://{esp32_ip}:81/stream"
cap = cv2.VideoCapture(stream_url)
if not cap.isOpened():
    print(f"ERROR: could not open MJPEG stream at {stream_url}")
    ser.close()
    sys.exit(1)
last_fire = 0.0
last_item = None
last_bin = None
last_confidence = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    item, bin_, confidence = classify_frame(frame)

    now = time.time()
    if bin_ in BIN_TO_COMMAND and (now - last_fire) >= COOLDOWN_SECONDS:
        command = BIN_TO_COMMAND[bin_]
        ser.write(f"{command}\n".encode())
        reply = ser.readline().decode(errors="ignore").strip()
        print(
            f"Item: {item} | Bin: {bin_} | Confidence: {confidence:.3f} | "
            f"Command: {command} | ESP32: {reply}"
        )
        subprocess.Popen(["say", bin_])
        last_fire = now
        last_item = item
        last_bin = bin_
        last_confidence = confidence

    display = frame
    if last_item is not None:
        display = draw_classification(display, last_item, last_bin, last_confidence)
    display = draw_prompt(display, "LIVE  |  Q: quit")
    cv2.imshow("FussyBin", display)

    if cv2.waitKey(FRAME_DELAY_MS) & 0xFF == ord("q"):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()
