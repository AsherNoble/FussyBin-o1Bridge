"""
FussyBin ESP32 camera — serial mode, base64 transport.
Mac sends 'CAPTURE\n', ESP32 replies with '<length>\n<base64 jpeg>\n'.
"""

import camera
import utime
import sys
import ubinascii

# ── Camera init ───────────────────────────────────────────────────────────────
try:
    camera.deinit()
except:
    pass
utime.sleep_ms(100)

try:
    camera.init(
        0,
        d0=4,  d1=5,  d2=18, d3=19,
        d4=36, d5=39, d6=34, d7=35,
        format=camera.JPEG,
        framesize=camera.FRAME_QVGA,  # 320x240 — faster over serial
        xclk_freq=camera.XCLK_10MHz,
        href=23, vsync=25,
        reset=-1, pwdn=-1,
        sioc=27, siod=26,
        xclk=21, pclk=22,
        fb_location=camera.PSRAM,
    )
    camera.quality(40)  # 10=best quality/largest, 63=worst/smallest; 40 is a good speed tradeoff
    camera.flip(1)
    camera.mirror(1)
except Exception as e:
    print("CAMERA_ERROR:", e)
    raise

camera.capture()  # discard first frame (warm-up)
print("READY")

# ── Command loop ──────────────────────────────────────────────────────────────
while True:
    cmd = sys.stdin.readline().strip()
    if cmd == "CAPTURE":
        jpg = camera.capture()
        if not jpg:
            print("ERROR")
            continue
        b64 = ubinascii.b2a_base64(jpg)  # bytes ending in \n
        print(len(b64))                  # send length first
        sys.stdout.write(b64.decode())   # send base64 data
