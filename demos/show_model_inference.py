import base64
import io
import sys
import time

sys.path.insert(0, r"C:\Users\sagun\Tvisha Your SkinCare Partner")

import model_inference as mi

MODEL_PATH = r"C:\Users\sagun\Tvisha Your SkinCare Partner\best_skin_model_8class.pth"
IMG_PATH = r"C:\Users\sagun\Tvisha Your SkinCare Partner\test-images\1.png"
OUT_DIR = r"C:\Users\sagun\Tvisha Your SkinCare Partner\demos"

print("=" * 70)
print("STEP 1: CLASS_NAMES  (the fixed, order-sensitive list)")
print("=" * 70)
for i, name in enumerate(mi.CLASS_NAMES):
    print(f"  index {i}: '{name}'  ->  display '{mi.DISPLAY_NAMES[name]}'  {mi.CONDITION_ICONS[name]}")
print()

print("=" * 70)
print("STEP 2: load_model(model_path)")
print("=" * 70)
t0 = time.time()
model = mi.load_model(MODEL_PATH)
t1 = time.time()
print(f"  model type        = {type(model)}")
print(f"  final layer        = {model.classifier}")
n_params = sum(p.numel() for p in model.parameters())
print(f"  total parameters   = {n_params:,}")
print(f"  model.training      = {model.training}   (False = eval mode, dropout OFF)")
print(f"  load time          = {t1 - t0:.2f}s")
print()

print("=" * 70)
print("STEP 3: predict(model, image_bytes)  -- on a REAL test photo")
print("=" * 70)
with open(IMG_PATH, "rb") as f:
    image_bytes = f.read()
print(f"  input photo         = {IMG_PATH}")
print(f"  raw bytes size       = {len(image_bytes):,} bytes")
print()

t0 = time.time()
result = mi.predict(model, image_bytes)
t1 = time.time()
print(f"  predict() time       = {t1 - t0:.2f}s")
print()

print("  ---- RAW RETURN VALUE of predict() ----")
print(f"  predicted_class    = '{result['predicted_class']}'")
print(f"  confidence          = {result['confidence']}%")
print(f"  icon               = {result['icon']}")
print(f"  gradcam_uri         = {'<None, generation failed>' if result['gradcam_uri'] is None else result['gradcam_uri'][:60] + '... (' + str(len(result['gradcam_uri'])) + ' chars total)'}")
print()

print("  ---- all_probs (all 8 classes, sorted highest to lowest) ----")
for p in result["all_probs"]:
    star = " <-- WINNER" if p["raw_label"] == result["predicted_class"] else ""
    bar = "#" * int(p["confidence"] / 2)
    print(f"  {p['confidence']:5.1f}%  {bar:<50} {p['label']}{star}")
print()

if result["gradcam_uri"]:
    print("=" * 70)
    print("STEP 4: decoding gradcam_uri back into an actual PNG file")
    print("=" * 70)
    header, b64data = result["gradcam_uri"].split(",", 1)
    print(f"  data URI header      = '{header}'")
    png_bytes = base64.b64decode(b64data)
    out_path = OUT_DIR + r"\gradcam_result.png"
    with open(out_path, "wb") as f:
        f.write(png_bytes)
    print(f"  decoded PNG size     = {len(png_bytes):,} bytes")
    print(f"  saved to             = {out_path}")
