# model_inference.py — explained for someone who has never written code

This is the file where the actual AI happens. Everything else in the
backend exists to get a clean, valid photo *to* this file, and to take what
this file produces and present it nicely afterward. This file itself does
three things: loads the trained model into memory, runs a photo through it
to get a prediction, and generates the Grad-CAM heatmap explaining that
prediction.

## Background ideas this file relies on

- **A neural network** is a kind of program that learns patterns from
  examples, rather than being explicitly told rules by a programmer. It's
  made of many small connected mathematical units, loosely inspired by
  neurons in a brain, arranged in layers. During training, the network is
  shown thousands of labeled example photos and gradually adjusts millions
  of internal numbers (called **weights**) so its predictions get closer
  and closer to the correct answers over time. Once training is done, those
  final weights are saved to a file — that's exactly what
  `best_skin_model_8class.pth` is: not "code" in the traditional sense, just
  millions of learned numbers.
- **EfficientNet-B0** is the specific, well-known neural network *design*
  (architecture) used here — the arrangement and connections of all those
  mathematical units. It wasn't invented for this project; it's a
  widely-used, published design that this project's training notebook
  (`dataset.ipynb`) fine-tuned on the 8-class skin dataset.
- **`timm`** and **`torch`** (PyTorch) are Python libraries for building,
  loading, and running neural networks. This project doesn't reimplement
  EfficientNet-B0's mathematics from scratch — `timm` already has a
  ready-made implementation of it, and PyTorch (`torch`) handles all the
  underlying number-crunching.
- **A "tensor"** is PyTorch's term for a grid of numbers (similar in spirit
  to a numpy array, mentioned in `face_validation.md`) — this is the format
  images (and everything else) need to be in before a PyTorch model can
  process them.
- **Inference** is the general term for "using an already-trained model to
  make a prediction," as opposed to **training**, which is the separate,
  much slower process of teaching the model in the first place. This file
  only ever does inference — training happened once, previously, inside
  `dataset.ipynb`, and its result was saved to the `.pth` file this code
  loads.

## The class list and lookup dictionaries (lines 11–44)

```python
CLASS_NAMES = [
    "Redness",
    "dark spots",
    ...
]
```

This is the list of the 8 exact condition names the model was trained to
recognize, in a very specific order. **This order is not arbitrary and must
never be changed** — during training, the images were loaded from folders
using a tool that automatically sorts the folder names alphabetically
(uppercase letters sort before lowercase in this sorting scheme, which is
why `"Redness"` — capital R — appears first, ahead of all the lowercase
class names). The trained model's internal output always comes back as 8
raw numbers in that exact same order, with no built-in labels attached —
position 0 in the model's output corresponds to whatever class was
alphabetically first during training, position 1 to the second, and so on.
If this list here were reordered, or a name were misspelled compared to the
original training folder names, the code would still run without crashing,
but every single prediction would be silently mislabeled — a genuinely
dangerous kind of bug, because nothing would look obviously wrong at a
glance.

```python
DISPLAY_NAMES = {
    "Redness": "Skin Redness",
    ...
}
CONDITION_ICONS = {
    "Redness": "🔴",
    ...
}
```

Two **dictionaries** mapping each raw class name to something more
presentable: a friendly display name, and an emoji icon. Keeping these
separate from `CLASS_NAMES` itself means the underlying, technically
important list stays exactly matched to the trained model, while the
*presentation* of each class (which could reasonably change — a different
icon, a friendlier name) can be edited freely without any risk of breaking
the model's actual predictions.

## The preprocessing pipeline (lines 46–50)

```python
_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

A neural network can't be handed a photo file directly — it needs the image
converted into a very specific numerical format, matching exactly how the
training images were prepared. `transforms.Compose([...])` chains several
processing steps together into one reusable pipeline (this is a PyTorch/
torchvision concept, not something built by hand here):

- **`Resize((224, 224))`** — every photo, regardless of its original size,
  is resized to exactly 224×224 pixels. EfficientNet-B0 expects a fixed
  input size, and 224×224 is the specific size it was trained on
  (matching the pretrained weights it originally started from before
  fine-tuning).
- **`ToTensor()`** — converts the image from PIL's image-object format into
  a PyTorch tensor, and also rescales every pixel's brightness value from
  the usual 0–255 range down to a 0.0–1.0 range, since neural networks
  generally work better with smaller, more evenly-scaled numbers.
- **`Normalize(mean=..., std=...)`** — shifts and rescales those 0.0–1.0
  values again, using a specific set of numbers (`[0.485, 0.456, 0.406]`
  and `[0.229, 0.224, 0.225]`, one value per red/green/blue color channel)
  that are the standard, well-known statistics of the huge general-purpose
  ImageNet dataset that EfficientNet-B0 was originally pretrained on,
  before this project fine-tuned it further. Using these exact same numbers
  here matters — the model's very first layers learned to expect input data
  centered around these specific statistics, so feeding it differently
  scaled data would confuse it.

The variable name starts with an underscore, `_transform`, following the
same "internal use only" convention explained in
`recommendation_engine.md`.

## `load_model(model_path)`

```python
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
```

Called exactly once, by `main.py`, when the server starts up.

`os.path.exists(model_path)` checks whether the given file actually exists
on disk before trying anything else. `raise FileNotFoundError(...)`
deliberately triggers an error with a clear, helpful message if it doesn't
— `main.py` is written to catch exactly this specific error and handle it
gracefully rather than letting the whole program crash (see `main.md`).

```python
model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=len(CLASS_NAMES))
```
This builds a *fresh, empty* EfficientNet-B0 network — correct shape and
structure, but with random, untrained internal numbers at this point, not
yet the actual trained weights. `pretrained=False` means "don't
automatically download the generic ImageNet-pretrained weights here" —
that step already happened once, during training in `dataset.ipynb`; this
code only needs the final, already-fine-tuned result, loaded explicitly a
few lines below. `num_classes=len(CLASS_NAMES)` tells `timm` this network
needs to end with exactly 8 possible outputs, matching `len(CLASS_NAMES)`
(the number of items in that list, which is 8) — not the 1,000-category
output that a standard, off-the-shelf ImageNet model would normally have.

```python
in_features = model.classifier.in_features
model.classifier = nn.Sequential(
    nn.Dropout(0.4),
    nn.Linear(in_features, len(CLASS_NAMES)),
)
```
This replaces the network's final decision-making layer. `model.classifier`
is the very last part of the network — the part responsible for turning
everything the network has "noticed" about the image into a final set of 8
scores, one per class. `in_features` reads how many numbers feed *into*
that final layer (a fixed property of the EfficientNet-B0 design itself).
`nn.Sequential(...)` builds a small new mini-pipeline to replace it,
containing two pieces:
- `nn.Dropout(0.4)` — during *training*, this step randomly ignores 40% of
  the incoming values on each pass, which is a well-known technique for
  preventing a model from over-relying on any one specific pattern and
  helps it generalize better to new, unseen photos rather than just
  memorizing the training set. (During inference, which is all this file
  ever does, dropout is automatically turned off — more on this below.)
- `nn.Linear(in_features, len(CLASS_NAMES))` — the actual final layer,
  mathematically combining all the incoming values down into exactly 8
  output numbers, one raw score per class.

```python
model.load_state_dict(torch.load(model_path, map_location="cpu"))
```
This is the step that actually loads the *trained* weights — the millions
of numbers learned during training — from the `.pth` file on disk, and
copies them into the freshly-built network structure from above. Without
this line, the network would still have the right shape but random,
meaningless internal numbers, and would produce useless, random
predictions. `map_location="cpu"` tells PyTorch to load the weights for use
on the computer's regular processor, rather than assuming a specific type
of graphics card (GPU) is available — making this code work correctly
whether or not the computer it's running on has a GPU.

```python
model.eval()
```
Switches the model into **evaluation mode** — the opposite of *training*
mode. Some parts of a neural network (like the `Dropout` layer above)
deliberately behave differently while training versus while actually being
used to make real predictions; `.eval()` turns off training-only behaviors
like dropout, ensuring predictions are consistent and use the model's full,
complete knowledge rather than a randomly-reduced subset of it.

## `predict(model, image_bytes)`

This is the function `main.py` calls for every single uploaded photo.

```python
img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
tensor = _transform(img).unsqueeze(0)
```
Opens the raw photo bytes as an image (the same `io.BytesIO` pattern
explained in `main.md`), forces it into standard RGB color format, then
runs it through the `_transform` pipeline described above, converting it
into the exact numerical format the model expects. `.unsqueeze(0)` adds an
extra dimension to the tensor — models are generally built to expect a
*batch* of images at once (even if, here, that batch always contains
exactly one image), so this step wraps the single image up as "a batch
containing one image," matching that expected shape.

```python
with torch.no_grad():
    probs = torch.softmax(model(tensor), dim=1)[0]
```
`model(tensor)` is the actual moment the neural network runs — feeding the
prepared image through every layer of the network and producing 8 raw
output scores. `torch.softmax(..., dim=1)` converts those 8 raw scores into
8 proper probabilities that all add up to exactly 100% — a mathematical
step that turns arbitrary numbers into a genuine "how confident is the
model in each option" distribution. `[0]` extracts the single result out of
the batch-of-one wrapper added by `.unsqueeze(0)` earlier.

`with torch.no_grad():` tells PyTorch "don't bother tracking the
information needed to later adjust the model's weights (which is only
relevant during training, never during inference)" — this makes the
calculation notably faster and use less memory, since PyTorch can skip
work that would only ever matter if this were a training step.

```python
idx = int(torch.argmax(probs).item())
```
`torch.argmax(probs)` finds the *position* of the single highest
probability among the 8 — in other words, which class the model is most
confident about. `.item()` converts that from a PyTorch-specific number
type into a plain ordinary Python number, and `int(...)` ensures it's
treated as a whole number, usable directly as a position in `CLASS_NAMES`.

```python
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
```
This builds the full list of all 8 results (not just the winning one),
which is what powers the "All Condition Scores" section on the results
page (see `result_html.md`). `range(len(CLASS_NAMES))` produces the numbers
0 through 7 — one for each class position. For each one, a dictionary is
built with a friendly `label`, the original `raw_label` (needed later to
match against the winning prediction — see `result_html.md`'s explanation
of the `★` marker), and `confidence` — the model's probability for that
specific class, multiplied by 100 to convert it to a percentage and rounded
to one decimal place with `round(..., 1)`.

`sorted(..., key=lambda x: x["confidence"], reverse=True)` then sorts that
whole list from highest confidence to lowest. `key=lambda x: x["confidence"]`
tells `sorted` exactly what to sort *by* — a small, throwaway function
(a **lambda**, Python's version of a very short unnamed function) that,
given one item `x` from the list, returns its `confidence` value for
comparison purposes. `reverse=True` flips the normal smallest-to-largest
order into largest-to-smallest.

```python
gradcam_uri = _gradcam(model, img, tensor, idx)
```
Calls the Grad-CAM function (explained fully below) to generate the
heatmap image, passing in the model, the original photo, the prepared
tensor, and which class index actually won — since Grad-CAM specifically
explains "why did the model pick *this* answer," it needs to know which
answer that was.

```python
return {
    "predicted_class": CLASS_NAMES[idx],
    "confidence":      round(probs[idx].item() * 100, 1),
    "icon":            CONDITION_ICONS.get(CLASS_NAMES[idx], "✨"),
    "all_probs":       all_probs,
    "gradcam_uri":     gradcam_uri,
}
```
Finally, everything gets bundled into one dictionary and returned —
this is the exact same `result` dictionary that `main.py` receives and
passes on to `result.html` (see `main.md`). `CONDITION_ICONS.get(CLASS_NAMES[idx], "✨")`
looks up the winning class's icon, with `"✨"` as a fallback default in the
unlikely case that class name wasn't found in the `CONDITION_ICONS`
dictionary for some reason.

## `_gradcam(model, original_img, tensor, target_idx)`

This is the function that generates the heatmap overlay shown on the
results page's before/after slider.

```python
try:
    import numpy as np
    from pytorch_grad_cam import GradCAM
    from pytorch_grad_cam.utils.image import show_cam_on_image
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    ...
except Exception:
    return None
```
The entire function body is wrapped in a `try`/`except Exception` block —
a deliberately broad safety net. Grad-CAM generation is more involved and
more likely to occasionally fail for unexpected technical reasons than the
core prediction step above; rather than letting any such failure crash the
whole `/analyze` request (which would deny the visitor their skin condition
result over what's really just a bonus visualization feature), any error
here is silently caught, and the function simply returns `None` instead.
`result_html.md` explains how the results page already gracefully handles
`gradcam_uri` being empty, falling back to just showing the plain photo
with no comparison slider.

```python
with GradCAM(model=model, target_layers=[model.conv_head]) as cam:
    grayscale = cam(
        input_tensor=tensor,
        targets=[ClassifierOutputTarget(target_idx)],
    )[0]
```
This uses the `pytorch_grad_cam` library (a ready-made implementation of
the Grad-CAM technique, not written from scratch here) to actually generate
the heatmap. Grad-CAM works by looking at *how much each part of one
specific internal layer's output influenced the model's final decision for
one specific class* — `target_layers=[model.conv_head]` tells it to
examine `conv_head`, the last convolutional (spatial, image-shaped) layer
inside EfficientNet-B0, right before the network flattens everything down
into the final 8 class scores. This is the standard, conventional layer to
target for this kind of network, since it's the last point where the
network's internal representation still has a meaningful width/height
layout corresponding to actual regions of the input image — later layers
lose that spatial structure entirely. `targets=[ClassifierOutputTarget(target_idx)]`
tells it specifically "explain the decision *for the class the model
actually predicted*," rather than for some other class. The result,
`grayscale`, is a heatmap: a grid of numbers indicating how strongly each
region of the image contributed to that specific prediction.

```python
orig_w, orig_h = original_img.size
img_arr = np.array(original_img.resize((224, 224)), dtype=np.float32) / 255.0
vis = show_cam_on_image(img_arr, grayscale, use_rgb=True)
```
`original_img.size` reads the photo's real, original width and height (the
one before it was resized down to 224×224 for the model). `img_arr` prepares
a 224×224 version of the photo as a numpy array of decimal numbers scaled
to a 0.0–1.0 range (`/ 255.0`), matching the scale Grad-CAM's own
`show_cam_on_image` helper function expects to receive. `show_cam_on_image`
does the actual visual work: blending the grayscale heatmap into a
colorful, easy-to-read overlay (warm colors for high-influence regions,
cool for low) painted directly on top of the photo.

```python
vis_img = Image.fromarray(vis).resize((orig_w, orig_h), Image.LANCZOS)
```
Converts the result back into a PIL image, then resizes it back up from
224×224 to the *original* photo's real dimensions (`orig_w, orig_h`, saved
earlier). This matters specifically because of the before/after slider on
the results page — both the original photo and the heatmap need to be
exactly the same size for the drag-to-compare effect in `result.js` to line
up correctly; without this resize, the heatmap would stay stuck at
224×224 while the original photo preview might be a completely different
size, making the comparison slider misaligned. `Image.LANCZOS` specifies
which resizing algorithm to use — a well-regarded option that tends to
produce smoother, higher-quality results when enlarging an image compared
to simpler/faster methods.

```python
buf = io.BytesIO()
vis_img.save(buf, format="PNG")
return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
```
The exact same "convert an in-memory image into a data URI" pattern
explained in detail in `main.md` for `preview_uri` — the finished heatmap
image is saved into an in-memory buffer, then encoded as a base64 data URI
string, ready to be dropped straight into an `<img src="...">` tag in
`result.html` with no separate image file ever needing to be saved to disk.
