"""
Classifies a single BGR frame against 50 common rubbish items.
Returns (item_label, bin_name, confidence_score).
"""

import cv2
import torch
import open_clip
import numpy as np
from PIL import Image

# ── Bin dictionary ────────────────────────────────────────────────────────────
# Format: "item label for CLIP": "Bin Name"

ITEMS = {
    # Recycling (yellow lid)
    "aluminium drink can":              "Recycling",
    "glass bottle":                     "Recycling",
    "plastic bottle":                   "Recycling",
    "plastic milk bottle":              "Recycling",
    "cardboard box":                    "Recycling",
    "cardboard":                        "Recycling",
    "newspaper":                        "Recycling",
    "magazine":                         "Recycling",
    "junk mail":                        "Recycling",
    "paper bag":                        "Recycling",
    "cereal box":                       "Recycling",
    "milk carton":                      "Recycling",
    "juice carton":                     "Recycling",
    "plastic food container":           "Recycling",
    "shampoo bottle":                   "Recycling",
    "detergent bottle":                 "Recycling",
    "tin can":                          "Recycling",
    "steel can":                        "Recycling",
    "aerosol can":                      "Recycling",
    "plastic bag":                      "Recycling",

    # General waste (red lid)
    "tissue":                           "General Waste",
    "paper towel":                      "General Waste",
    "disposable coffee cup":            "General Waste",
    "styrofoam cup":                    "General Waste",
    "styrofoam container":              "General Waste",
    "plastic straw":                    "General Waste",
    "plastic cutlery":                  "General Waste",
    "chip packet":                      "General Waste",
    "candy wrapper":                    "General Waste",
    "cling wrap":                       "General Waste",
    "pizza box":                        "General Waste",
    "dirty takeaway container":         "General Waste",
    "cigarette butt":                   "General Waste",
    "pen":                              "General Waste",
    "rubber band":                      "General Waste",

    # Green / organic (green lid)
    "apple core":                       "Green Bin",
    "orange peel":                      "Green Bin",
    "vegetable scraps":                 "Green Bin",
    "coffee grounds":                   "Green Bin",
    "tea bag":                          "Green Bin",
    "egg shells":                       "Green Bin",
    "garden clippings":                 "Green Bin",
    "leaves":                           "Green Bin",
    "grass clippings":                  "Green Bin",
    "bread":                            "Green Bin",
    "banana peel":                      "Green Bin",
    "food scraps":                      "Green Bin",
}

LABELS = list(ITEMS.keys())
BINS   = list(ITEMS.values())

# ── Load CLIP ─────────────────────────────────────────────────────────────────
print("Loading CLIP model...")
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="openai"
)
tokenizer = open_clip.get_tokenizer("ViT-B-32")
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")
model = model.to(device)
model.eval()

with torch.no_grad():
    text_tokens   = tokenizer(LABELS)
    text_features = model.encode_text(text_tokens.to(device))
    text_features /= text_features.norm(dim=-1, keepdim=True)


def classify_frame(frame):
    """Classify a BGR numpy frame. Returns (item, bin_, confidence)."""
    rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil   = Image.fromarray(rgb)
    image = preprocess(pil).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features  = model.encode_image(image)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        similarities    = (image_features @ text_features.T).squeeze(0)
        best_idx        = similarities.argmax().item()
        confidence      = similarities[best_idx].item()

    return LABELS[best_idx], BINS[best_idx], confidence
