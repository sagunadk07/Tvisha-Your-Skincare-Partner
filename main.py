import argparse
import base64
import io
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from PIL import Image, UnidentifiedImageError

from face_validation import validate_and_crop_face
from model_inference import load_model, predict, CLASS_NAMES, DISPLAY_NAMES, CONDITION_ICONS
from recommendation_engine import get_recommendation

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tvisha-dev-secret")

MODEL_PATH = "best_skin_model_8class.pth"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

try:
    model = load_model(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")
except FileNotFoundError as e:
    model = None
    print(f"WARNING: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    conditions = [
        {"name": DISPLAY_NAMES[c], "icon": CONDITION_ICONS[c]}
        for c in CLASS_NAMES
    ]
    return render_template("about.html", conditions=conditions)


@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if model is None:
        flash("Model not loaded. Place best_skin_model_8class.pth in the project root.")
        return redirect(url_for("scanner"))

    file = request.files.get("skin_image")
    if not file or file.filename == "":
        flash("Please select an image before submitting.")
        return redirect(url_for("scanner"))

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash("Unsupported file type. Please upload PNG, JPG, JPEG, or WEBP.")
        return redirect(url_for("scanner"))

    image_bytes = file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
        flash("File too large. Maximum size is 10 MB.")
        return redirect(url_for("scanner"))

    try:
        uploaded_image = Image.open(io.BytesIO(image_bytes))
        uploaded_image.load()
    except UnidentifiedImageError:
        flash("Could not read that image. Please try a different file.")
        return redirect(url_for("scanner"))

    face_image, face_error = validate_and_crop_face(uploaded_image)
    if face_error:
        flash(face_error)
        return redirect(url_for("scanner"))

    face_buf = io.BytesIO()
    face_image.save(face_buf, format="PNG")
    face_bytes = face_buf.getvalue()

    result = predict(model, face_bytes)
    recommendation = get_recommendation(result["predicted_class"])

    preview_uri = "data:image/png;base64," + base64.b64encode(face_bytes).decode()

    return render_template(
        "result.html",
        prediction=result,
        recommendation=recommendation,
        preview_uri=preview_uri,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
