#!/usr/bin/env python3
import sys
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import cv2
from src.rubbish_item_classifier import classify_frame

if len(sys.argv) != 2:
    print("Usage: python scripts/classify_with_filepath.py <image_path>")
    sys.exit(1)

frame = cv2.imread(sys.argv[1])
if frame is None:
    print(f"Error: could not read image '{sys.argv[1]}'")
    sys.exit(1)

start = time.perf_counter()
item, bin_, confidence = classify_frame(frame)
elapsed = time.perf_counter() - start
print(f"\n  Item  : {item}")
print(f"  Bin   : {bin_}")
print(f"  Score : {confidence:.3f}")
print(f"  Time  : {elapsed:.3f}s")
