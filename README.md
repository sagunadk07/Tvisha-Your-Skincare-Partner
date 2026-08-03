# Tvisha — Your Skincare Partner

An AI-powered skin analysis web app. Upload a photo, and Tvisha detects one of 8 common
skin conditions using a fine-tuned EfficientNet-B0 model, shows a Grad-CAM heatmap of
what the model focused on, and returns personalized ingredient/product/routine advice.

## Features

- **Photo validation** before inference — rejects images that are too blurry, too
  dark/bright, or contain zero/multiple detected faces (Haar cascade face + eye detection).
- **8-class skin condition classifier** (EfficientNet-B0, via `timm`): redness, dark
  spots, inflammatory acne, blackheads, whiteheads, pigmentation, enlarged pores, wrinkles.
- **Grad-CAM visualization** — a before/after slider comparing your photo against the
  model's attention heatmap.
- **Personalized recommendations** — ingredients, product suggestions, and skincare
  advice pulled from `static/data/skin_recommendations.csv`, keyed by predicted condition.

## Tech stack

- Flask (server + Jinja templates)
- PyTorch / `timm` (EfficientNet-B0 classifier)
- OpenCV (face/eye detection, blur/brightness checks)
- `pytorch-grad-cam` (heatmap generation)
- Pillow (image I/O)

## Project structure

```
main.py                     Flask app: routes, upload handling, orchestration
face_validation.py          Blur/brightness/face checks + face-crop before inference
model_inference.py          Model loading, prediction, Grad-CAM overlay generation
recommendation_engine.py    Looks up ingredient/product/advice recommendations by class
static/data/
  skin_recommendations.csv  Recommendation content, one row per condition
templates/
  base.html, index.html,
  scanner.html, result.html,
  about.html                 Jinja templates
static/css/app.css           Design system used by result.html (cream/rose palette)
best_skin_model_8class.pth   Trained model weights (required, see below)
```

> **Note:** `app.py`, `templates/login.html`, `static/css/style.css`, and
> `static/js/main.js` are leftover/in-progress files not wired into the current app —
> `main.py` is the real entry point. `templates/index.html`, `scanner.html`, and
> `about.html` currently render against `base.html`'s older Bootstrap-based styling,
> while `result.html` alone has been migrated to the newer `app.css` design system.

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

Place the trained model weights file, `best_skin_model_8class.pth`, in the project root
(same directory as `main.py`). The app will start with a warning and disable analysis if
the file is missing.

## Running

```bash
python main.py --port 5001
```

Then visit `http://127.0.0.1:5001/`.

## Routes

| Route       | Method | Description                                      |
|-------------|--------|---------------------------------------------------|
| `/`         | GET    | Landing page                                       |
| `/scanner`  | GET    | Upload form                                         |
| `/analyze`  | POST   | Validates + classifies an uploaded photo, renders `result.html` |
| `/about`    | GET    | About page, lists all 8 detectable conditions      |

## Disclaimer

This tool is for informational purposes only and is not a medical diagnosis. Consult a
dermatologist for professional skincare advice.
