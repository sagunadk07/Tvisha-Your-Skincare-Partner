import base64
import io
import os

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

# Short display names for the probability chart
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

# Icon shown on the result page badge and the About page conditions grid
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


def load_model(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file '{model_path}' not found. "
            "Place best_skin_model_8class.pth in the project root."
        )
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=len(CLASS_NAMES))
    in_features = model.classifier.in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(in_features, len(CLASS_NAMES)),
    )
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    return model


def predict(model, image_bytes: bytes) -> dict:
    """
    Returns a dict with:
      predicted_class  — top class name
      confidence       — confidence % (0–100)
      all_probs        — list of {label, confidence} for all 8 classes, sorted high→low
      gradcam_uri      — data URI of the Grad-CAM heatmap overlay (or None)
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(img).unsqueeze(0)

    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0]

    idx = int(torch.argmax(probs).item())

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

    # Grad-CAM runs OUTSIDE torch.no_grad so gradients can flow
    gradcam_uri = _gradcam(model, img, tensor, idx)

    return {
        "predicted_class": CLASS_NAMES[idx],
        "confidence":      round(probs[idx].item() * 100, 1),
        "icon":            CONDITION_ICONS.get(CLASS_NAMES[idx], "✨"),
        "all_probs":       all_probs,
        "gradcam_uri":     gradcam_uri,
    }


def _gradcam(model, original_img, tensor, target_idx):
    """Generate a Grad-CAM heatmap overlay and return it as a data URI."""
    try:
        import numpy as np
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

        # conv_head is the last spatial conv layer in EfficientNet-B0 (outputs 1280-ch feature map)
        with GradCAM(model=model, target_layers=[model.conv_head]) as cam:
            grayscale = cam(
                input_tensor=tensor,
                targets=[ClassifierOutputTarget(target_idx)],
            )[0]

        orig_w, orig_h = original_img.size
        img_arr = np.array(original_img.resize((224, 224)), dtype=np.float32) / 255.0
        vis = show_cam_on_image(img_arr, grayscale, use_rgb=True)

        # Scale the heatmap back to the original image size so the slider
        # comparison aligns correctly (both images share the same dimensions).
        vis_img = Image.fromarray(vis).resize((orig_w, orig_h), Image.LANCZOS)

        buf = io.BytesIO()
        vis_img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None
