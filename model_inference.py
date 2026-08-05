import base64
import io
import os
import time

import torch
import torch.nn as nn
import timm
from torchvision import transforms
from PIL import Image

CLASS_NAMES = [
    "Redness",
    "dark spots",
    "inflammatory acne",
    "non inflammatory acne black heads",
    "non inflammatory acne white heads",
    "pigmentation",
    "pores",
    "wrinkles",
]

DISPLAY_NAMES = {
    "Redness":                                  "Skin Redness",
    "dark spots":                               "Dark Spots",
    "inflammatory acne":                        "Inflammatory Acne",
    "non inflammatory acne black heads":        "Blackheads",
    "non inflammatory acne white heads":        "Whiteheads",
    "pigmentation":                             "Pigmentation",
    "pores":                                    "Enlarged Pores",
    "wrinkles":                                 "Fine Lines & Wrinkles",
}

CONDITION_ICONS = {
    "Redness":                                  "🔴",
    "dark spots":                               "🌑",
    "inflammatory acne":                        "🔥",
    "non inflammatory acne black heads":        "⚫",
    "non inflammatory acne white heads":        "⚪",
    "pigmentation":                             "🎨",
    "pores":                                    "🔬",
    "wrinkles":                                 "〰️",
}

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

_LOG_PREFIX = "[model_inference]"


def _log(message: str) -> None:
    try:
        print(f"{_LOG_PREFIX} {message}")
    except UnicodeEncodeError:
        # Some Windows consoles use a narrow codepage (e.g. cp1252) that can't
        # encode certain characters (box-drawing lines, some punctuation).
        # Fall back to a plain-ASCII version rather than crashing the request.
        print(f"{_LOG_PREFIX} {message}".encode("ascii", errors="replace").decode("ascii"))


def load_model(model_path: str):
    _log(f"STEP 1  Looking for model weights at '{model_path}'")
    if not os.path.exists(model_path):
        _log("STEP 1  NOT FOUND - aborting load")
        raise FileNotFoundError(
            f"Model file '{model_path}' not found. "
            "Place best_skin_model_8class.pth in the project root."
        )
    _log("STEP 2  Building EfficientNet-B0 architecture (8-class head)")
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=len(CLASS_NAMES))
    in_features = model.classifier.in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(in_features, len(CLASS_NAMES)),
    )
    _log("STEP 3  Loading trained weights into the architecture")
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    _log("STEP 4  Switching model to eval mode (disables dropout)")
    model.eval()
    _log("Model ready.\n")
    return model


def predict(model, image_bytes: bytes) -> dict:
    start = time.time()
    _log("---- New prediction ----------------------------")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    _log(f"STEP 1  Loaded photo: {img.size[0]}x{img.size[1]} px, RGB")

    tensor = _transform(img).unsqueeze(0)
    _log(f"STEP 2  Preprocessed to tensor {tuple(tensor.shape)} "
         f"(resized to 224x224, normalized with ImageNet mean/std)")

    with torch.no_grad():
        probs_orig = torch.softmax(model(tensor), dim=1)[0]
        # Test-time augmentation: also classify the horizontally-flipped photo and average the
        # two probability distributions. Validated in dataset.ipynb (step 12) to give a small,
        # free accuracy bump over a single forward pass. dim 3 = width, so this is a horizontal flip.
        tensor_flipped = torch.flip(tensor, dims=[3])
        probs_flipped = torch.softmax(model(tensor_flipped), dim=1)[0]
        probs = (probs_orig + probs_flipped) / 2
    _log(f"STEP 3  Forward pass complete, original + flipped averaged (TTA) ({time.time() - start:.2f}s so far)")

    idx = int(torch.argmax(probs).item())
    orig_idx = int(torch.argmax(probs_orig).item())
    if orig_idx != idx:
        _log(f"        note: TTA changed the top prediction from '{CLASS_NAMES[orig_idx]}' to '{CLASS_NAMES[idx]}'")

    all_probs = sorted(
        [
            {
                "label":      DISPLAY_NAMES.get(CLASS_NAMES[i], CLASS_NAMES[i]),
                "raw_label":  CLASS_NAMES[i],
                "confidence": round(probs[i].item() * 100, 1),
            }
            for i in range(len(CLASS_NAMES))
        ],
        key=lambda x: x["confidence"],
        reverse=True,
    )

    _log("STEP 4  Softmax confidence per class (averaged across original + flipped):")
    for p in all_probs:
        marker = "*" if p["raw_label"] == CLASS_NAMES[idx] else " "
        _log(f"        {marker} {p['label']:<24} {p['confidence']:>5.1f}%")

    _log(f"STEP 5  Top prediction: {CLASS_NAMES[idx]} ({round(probs[idx].item() * 100, 1)}% confidence)")

    _log("STEP 6  Generating Grad-CAM heatmap on the original (non-flipped) photo, "
         "for the TTA-averaged top class (needs gradients, so it runs outside no_grad)")
    gradcam_uri = _gradcam(model, img, tensor, idx)
    if gradcam_uri:
        _log(f"STEP 7  Grad-CAM heatmap ready - total elapsed {time.time() - start:.2f}s\n")
    else:
        _log(f"STEP 7  Grad-CAM unavailable - falling back to plain photo "
             f"(total elapsed {time.time() - start:.2f}s)\n")

    return {
        "predicted_class": CLASS_NAMES[idx],
        "confidence":      round(probs[idx].item() * 100, 1),
        "icon":            CONDITION_ICONS.get(CLASS_NAMES[idx], "✨"),
        "all_probs":       all_probs,
        "gradcam_uri":     gradcam_uri,
    }


def _gradcam(model, original_img, tensor, target_idx):
    try:
        import numpy as np
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

        _log("        target layer: model.conv_head (last conv layer before pooling)")
        with GradCAM(model=model, target_layers=[model.conv_head]) as cam:
            grayscale = cam(
                input_tensor=tensor,
                targets=[ClassifierOutputTarget(target_idx)],
            )[0]
        _log("        heatmap computed for the predicted class")

        orig_w, orig_h = original_img.size
        img_arr = np.array(original_img.resize((224, 224)), dtype=np.float32) / 255.0
        vis = show_cam_on_image(img_arr, grayscale, use_rgb=True)

        vis_img = Image.fromarray(vis).resize((orig_w, orig_h), Image.LANCZOS)
        _log(f"        overlay composited and resized back to {orig_w}x{orig_h}")

        buf = io.BytesIO()
        vis_img.save(buf, format="PNG")
        _log("        encoded overlay as base64 PNG data URI")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        _log(f"        Grad-CAM failed ({e.__class__.__name__}: {e}) - skipping")
        return None
