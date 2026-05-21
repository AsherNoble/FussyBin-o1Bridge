#!/usr/bin/env python3
"""Evaluate classifier accuracy against the sample images in images/.

Ground truth is inferred from filename prefix:
  banana_peel_*    -> Green Bin
  coffee_cup_*     -> General Waste
  coffee_grounds_* -> Green Bin
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import cv2
from src.rubbish_item_classifier import classify_frame

EXPECTED = {
    "banana_peel":    "Green Bin",
    "coffee_cup":     "General Waste",
    "coffee_grounds": "Green Bin",
}


def expected_bin(filename: str) -> str | None:
    """Infer the expected bin from a filename like 'banana_peel_1.jpeg'."""
    stem = filename.rsplit(".", 1)[0]
    for prefix, bin_ in EXPECTED.items():
        if stem.startswith(prefix):
            return bin_
    return None


def main():
    images_dir = pathlib.Path(__file__).parent.parent / "images"
    image_paths = sorted(images_dir.glob("*.jpeg")) + sorted(images_dir.glob("*.jpg"))

    if not image_paths:
        print(f"No images found in {images_dir}")
        sys.exit(1)

    correct = 0
    skipped = 0
    print(f"{'image':<28} {'predicted bin':<15} {'expected':<15} {'item':<26} {'conf':>6}  ok")
    print("-" * 100)

    for path in image_paths:
        frame = cv2.imread(str(path))
        if frame is None:
            print(f"{path.name:<28} (could not read)")
            continue

        expected = expected_bin(path.name)
        if expected is None:
            print(f"{path.name:<28} (no ground truth - skipping)")
            skipped += 1
            continue

        item, bin_, confidence = classify_frame(frame)
        is_correct = bin_ == expected
        marker = "Y" if is_correct else "N"
        print(f"{path.name:<28} {bin_:<15} {expected:<15} {item:<26} {confidence:>6.3f}  {marker}")
        if is_correct:
            correct += 1

    graded = len(image_paths) - skipped
    if graded > 0:
        accuracy = 100 * correct / graded
        print(f"\nAccuracy: {correct}/{graded} ({accuracy:.1f}%)" + (f", {skipped} skipped" if skipped else ""))


if __name__ == "__main__":
    main()
