"""Tests for src.rubbish_item_classifier."""
import pathlib
import sys
import unittest

import cv2

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.rubbish_item_classifier import classify_frame

IMAGES_DIR = pathlib.Path(__file__).parent.parent / "images"


class TestRubbishItemClassifier(unittest.TestCase):

    def test_banana_peel_classified_as_green_bin(self):
        frame = cv2.imread(str(IMAGES_DIR / "banana_peel_1.jpeg"))
        self.assertIsNotNone(frame, "sample image not found")
        item, bin_, confidence = classify_frame(frame)
        self.assertEqual(
            bin_, "Green Bin",
            msg=f"expected Green Bin, got item={item!r}, bin={bin_!r}, conf={confidence:.3f}",
        )

    def test_coffee_cup_classified_as_general_waste(self):
        frame = cv2.imread(str(IMAGES_DIR / "coffee_cup_1.jpeg"))
        self.assertIsNotNone(frame, "sample image not found")
        item, bin_, confidence = classify_frame(frame)
        self.assertEqual(
            bin_, "General Waste",
            msg=f"expected General Waste, got item={item!r}, bin={bin_!r}, conf={confidence:.3f}",
        )

    def test_unsure_fallback_below_threshold(self):
        frame = cv2.imread(str(IMAGES_DIR / "banana_peel_1.jpeg"))
        self.assertIsNotNone(frame, "sample image not found")
        # Force the fallback by passing a threshold no real prediction can clear.
        item, bin_, confidence = classify_frame(frame, threshold=0.999)
        self.assertEqual(bin_, "Unsure")


if __name__ == "__main__":
    unittest.main()
