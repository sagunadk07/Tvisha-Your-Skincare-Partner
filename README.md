# Tvisha — Your Skincare Partner

An AI-powered skin analysis web app. Upload a photo, and Tvisha detects one of 8 common
skin conditions using a fine-tuned EfficientNet-B0 model, shows a Grad-CAM heatmap of
what the model focused on, and returns personalized ingredient/product/routine advice.

## Features

- **Accounts** — signup/login/logout, session-based auth (SQLite-backed via `auth.py`).
  The first account ever created becomes an admin automatically; admins get a `/admin`
  panel to view and delete users. Scanning a photo requires being logged in.
- **CSRF protection** on every form (login, signup, admin delete, and the photo upload
  itself) via `Flask-WTF`.
- **Photo validation** before inference — rejects images that are too blurry, too
  dark/bright, or contain zero/multiple detected faces (Haar cascade face + eye detection).
- **8-class skin condition classifier** (EfficientNet-B0, via `timm`): redness, dark
  spots, inflammatory acne, blackheads, whiteheads, pigmentation, enlarged pores, wrinkles.
  Predictions use test-time augmentation (original + horizontally-flipped photo, averaged)
  for a small accuracy boost.
- **Grad-CAM visualization** — a before/after slider comparing your photo against the
  model's attention heatmap.
- **Personalized recommendations** — ingredients, product suggestions, and skincare
  advice pulled from `static/data/skin_recommendations.csv`, keyed by predicted condition.

## Tech stack

- Flask (server + Jinja templates), Flask-WTF (CSRF)
- SQLite (via `auth.py`, `werkzeug.security` for password hashing) — user accounts
- PyTorch / `timm` (EfficientNet-B0 classifier)
- OpenCV (face/eye detection, blur/brightness checks)
- `pytorch-grad-cam` (heatmap generation)
- Pillow (image I/O)
- pytest (tests)

## Project structure

```
main.py                     Flask app: routes, auth gating, upload handling, orchestration
auth.py                     SQLite-backed user accounts: create/verify/list/delete, admin flag
face_validation.py          Blur/brightness/face checks + face-crop before inference
model_inference.py          Model loading, prediction (with TTA), Grad-CAM overlay generation
recommendation_engine.py    Looks up ingredient/product/advice recommendations by class
static/data/
  skin_recommendations.csv  Recommendation content, one row per condition
templates/
  base.html, index.html,
  scanner.html, result.html,
  about.html, login.html,
  signup.html, admin.html    Jinja templates
static/css/app.css           Design system used by result.html (cream/rose palette)
best_skin_model_8class.pth   Trained model weights (required, see below)
users.db                     SQLite user database (gitignored, created on first run)
tests/                       pytest suite for face_validation.py and recommendation_engine.py
```

> **Note:** `templates/index.html`, `scanner.html`, `about.html`, `login.html`,
> `signup.html`, and `admin.html` all render against `base.html`'s Bootstrap-based
> styling, while `result.html` alone has been migrated to the newer `app.css` design
> system — the two haven't been unified yet, so the result page looks visually
> different from the rest of the site.

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

Place the trained model weights file, `best_skin_model_8class.pth`, in the project root
(same directory as `main.py`). The app will start with a warning and disable analysis if
the file is missing.

Set a `SECRET_KEY` environment variable before deploying anywhere real — without it, the
app generates a random key each time it starts (fine for local dev; every existing
session gets invalidated on restart, which is why this isn't suitable for production).

## Running

```bash
python main.py --port 5001
```

Then visit `http://127.0.0.1:5001/`. Create an account via `/signup` before you can scan
a photo — the first account created becomes an admin automatically.

## Running tests

```bash
pytest tests/
```

Covers `face_validation.py` (blur/brightness thresholds, and the face/eye-detection
branching logic via mocked Haar cascades) and `recommendation_engine.py` (CSV lookup,
including a regression check that every class the model can predict has a matching row
in the real recommendations CSV).

## Routes

| Route                     | Method     | Description                                      |
|----------------------------|-----------|---------------------------------------------------|
| `/`                        | GET       | Landing page (upload form if logged in, login prompt otherwise) |
| `/scanner`                 | GET       | Upload form                                        |
| `/analyze`                 | POST      | Requires login. Validates + classifies an uploaded photo, renders `result.html` |
| `/about`                   | GET       | About page, lists all 8 detectable conditions      |
| `/signup`, `/login`        | GET, POST | Account creation / sign-in                         |
| `/logout`                  | GET       | Clears the session                                 |
| `/admin`                   | GET       | Admin-only: lists all users                        |
| `/admin/delete/<user_id>`  | POST      | Admin-only: deletes a user (can't delete yourself or the last remaining admin) |

## Disclaimer

This tool is for informational purposes only and is not a medical diagnosis. Consult a
dermatologist for professional skincare advice.
