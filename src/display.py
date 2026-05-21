"""Shared overlay helpers for the live classification scripts."""

import cv2

BIN_COLOURS = {
    "Recycling":     (0, 200, 255),
    "General Waste": (0,   0, 220),
    "Green Bin":     (0, 180,   0),
    "Unsure":        (180, 180, 180),
}


def draw_prompt(frame, text="SPACE: classify  |  Q: quit"):
    """Return a BGR copy of `frame` with the keybind prompt bar overlaid at the top."""
    result = frame.copy()
    cv2.putText(result, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return result


def draw_classification(frame, item, bin_, confidence):
    """Return a BGR copy of `frame` with item / target-bin / confidence overlaid."""
    result = frame.copy()
    colour = BIN_COLOURS.get(bin_, (255, 255, 255))
    cv2.putText(result, item, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colour, 2)
    cv2.putText(result, f"-> {bin_}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, colour, 3)
    cv2.putText(result, f"confidence: {confidence:.2f}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    return result
