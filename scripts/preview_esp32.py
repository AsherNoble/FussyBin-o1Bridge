#!/usr/bin/env python3
"""
Live preview of ESP32 camera over USB serial.
Make sure PyCharm's MicroPython REPL is disconnected before running.
"""
import base64
import serial
import cv2
import numpy as np

SERIAL_PORT = "/dev/cu.usbserial-1130"
BAUD_RATE   = 115200

def fetch_frame(ser):
    ser.write(b"CAPTURE\n")
    line = ser.readline().decode(errors="ignore").strip()
    if not line.isdigit():
        print("Unexpected response:", repr(line))
        return None
    b64 = ser.read(int(line))
    jpg = base64.b64decode(b64)
    return cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

print(f"Connecting to ESP32 on {SERIAL_PORT}...")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)

while True:
    line = ser.readline().decode(errors="ignore").strip()
    if line == "READY":
        ser.reset_input_buffer()  # clear any leftover boot bytes
        print("Camera ready. Press Q to quit.")
        break

while True:
    frame = fetch_frame(ser)
    if frame is not None:
        cv2.imshow("ESP32 Preview", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

ser.close()
cv2.destroyAllWindows()
