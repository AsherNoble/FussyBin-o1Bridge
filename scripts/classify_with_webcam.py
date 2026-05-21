#!/usr/bin/env python3
import sys
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import cv2
from src.rubbish_item_classifier import classify_frame
from src.display import draw_prompt, draw_classification

cap = cv2.VideoCapture(0)
print("Model ready. Press SPACE to classify, Q to quit.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

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

cap.release()
cv2.destroyAllWindows()
