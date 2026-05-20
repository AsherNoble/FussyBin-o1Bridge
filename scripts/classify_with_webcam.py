#!/usr/bin/env python3
import sys
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import cv2
from src.rubbish_item_classifier import classify_frame

cap = cv2.VideoCapture(0)
print("Model ready. Press SPACE to classify, Q to quit.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    display = frame.copy()
    cv2.putText(display, "SPACE: classify  |  Q: quit",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("BinBot", display)

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
            "Recycling":    (0, 200, 255),
            "General Waste":(0,   0, 220),
            "Green Bin":    (0, 180,   0),
        }.get(bin_, (255, 255, 255))

        cv2.putText(result_frame, item,
                    (10,  60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colour, 2)
        cv2.putText(result_frame, f"-> {bin_}",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, colour, 3)
        cv2.putText(result_frame, f"confidence: {confidence:.2f}",
                    (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("BinBot", result_frame)
        cv2.waitKey(2000)

cap.release()
cv2.destroyAllWindows()
