# face_validation.py — explained for someone who has never written code

This file's only job is to look at a photo someone just uploaded and decide:
"is this photo actually usable?" If yes, it may also trim the photo down to
just the useful part. If no, it hands back a plain-English reason why, so
`main.py` can show that message to the visitor and ask them to try again.

## Ideas this file relies on

- **A library** is a bundle of ready-made code that someone else wrote,
  which you can `import` into your own project instead of writing that
  functionality yourself from scratch. This file uses two: `cv2` (OpenCV, a
  very well-known library for working with images and video) and `numpy`
  (a library for doing fast math on big grids of numbers).
- **An image, to a computer, is just a grid of numbers.** A color photo is
  really a big 3D grid: for every single pixel (a tiny dot of color), there
  are three numbers recording how much red, green, and blue light it has. A
  black-and-white (grayscale) photo is simpler — one number per pixel,
  saying how bright or dark it is, usually from `0` (pure black) to `255`
  (pure white).
- **A function's "type hints"**, like `(gray_image: np.ndarray) -> bool`,
  are notes (not strictly enforced by Python, but very useful for a human
  reading the code) saying what kind of value goes in and what kind comes
  out. `np.ndarray` means "a numpy grid of numbers" (like an image). `bool`
  means the function returns either `True` or `False`. `str | None` means
  "either some text, or nothing at all" — the `|` means "or."

## Setting up the face detectors (lines 1–6)

```python
import cv2
import numpy as np
from PIL import Image

FACE_DETECTOR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
EYE_DETECTOR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
```

`cv2.CascadeClassifier(...)` loads a **Haar cascade** — a ready-made,
pre-built pattern detector that comes bundled with OpenCV. Nobody in this
project trained it; it already exists, and this line just loads it into
memory so it can be used. A Haar cascade works by looking for simple
patterns of light and dark rectangles — for example, "the area where an eye
socket usually is tends to be darker than the cheek just below it." It
doesn't "understand" faces the way a modern AI does; it's really just a
very fast, clever set of brightness-pattern rules, checked in stages, most
of which reject an area immediately if it doesn't look face-like at all
(which is why it's called a "cascade" — like a waterfall of checks). This
happens once, right when the file is first loaded, rather than being redone
for every single photo, since it's a bit of setup work best done just once.

`FACE_DETECTOR` looks for whole faces; `EYE_DETECTOR` looks specifically for
eyes, and is used later as an extra sanity check.

## The settings (lines 8–11)

```python
EXTRA_SPACE_AROUND_FACE = 0.3
BLUR_THRESHOLD = 100.0
MIN_BRIGHTNESS = 40
MAX_BRIGHTNESS = 220
```

Four numbers, each controlling one of the checks further down:
- `EXTRA_SPACE_AROUND_FACE` — when a face is found and cropped to, this adds
  30% extra room around it (as a fraction of the face's own size), so the
  crop doesn't cut off right at the edge of the face and includes a little
  forehead/cheek/jaw around it.
- `BLUR_THRESHOLD` — the cutoff number used to decide if a photo counts as
  "too blurry" (explained fully below).
- `MIN_BRIGHTNESS` / `MAX_BRIGHTNESS` — the acceptable range for how bright
  the photo can be on average, out of 255.

## `is_too_blurry(gray_image)`

```python
def is_too_blurry(gray_image: np.ndarray) -> bool:
    variance = cv2.Laplacian(gray_image, cv2.CV_64F).var()
    return variance < BLUR_THRESHOLD
```

This function measures sharpness using a classic, well-known trick.
`cv2.Laplacian(gray_image, cv2.CV_64F)` runs a mathematical filter called a
Laplacian over the grayscale image. Without getting into the exact math: a
Laplacian filter reacts strongly wherever brightness changes suddenly
between neighboring pixels — in other words, wherever there's a sharp
*edge* in the photo (like the crisp boundary of a mole, or a strand of
hair). A photo that's in sharp focus is full of these strong, clearly
defined edges everywhere. A blurry photo has smooth, gradual transitions
instead — its edges are "soft," so the Laplacian filter's response to it is
weak almost everywhere.

`.var()` then calculates the **variance** of all those Laplacian values —
variance is a standard statistics measurement of how spread out / varied a
set of numbers is. A sharp photo, full of strong edges in some places and
almost none in flat areas (like skin), produces Laplacian values that swing
between very high and very low — high variance. A blurry photo's Laplacian
values are all fairly similar and small everywhere — low variance. So this
one number, `variance`, ends up naturally high for sharp photos and low for
blurry ones.

`return variance < BLUR_THRESHOLD` then simply checks: is that number below
our cutoff of `100.0`? If so, the function returns `True` (yes, it's too
blurry). `100.0` is a commonly recommended starting point for this
particular technique, taken from general practice rather than measured
specifically from this project's own photos — a reasonable default that
could be adjusted later if it turns out too strict or too lenient in
practice.

## `is_bad_brightness(gray_image)`

```python
def is_bad_brightness(gray_image: np.ndarray) -> str | None:
    average_brightness = gray_image.mean()
    if average_brightness < MIN_BRIGHTNESS:
        return "This photo is too dark. Please retake it somewhere with better lighting."
    if average_brightness > MAX_BRIGHTNESS:
        return "This photo is too bright/overexposed. Please retake it with softer, more even lighting."
    return None
```

Much simpler than the blur check. `gray_image.mean()` calculates the plain
mathematical average of every single pixel's brightness value in the whole
photo, giving one overall brightness score from 0 (all black) to 255 (all
white). If that average is below `MIN_BRIGHTNESS` (40), the photo is judged
too dark to make out real skin detail, and the function returns an error
message explaining that. If it's above `MAX_BRIGHTNESS` (220), it's judged
overexposed/washed out, and a different message is returned. If neither
problem applies, the function returns `None` — Python's built-in way of
representing "nothing," used here to mean "no problem found."

Notice this function sometimes returns text (a `str`) and sometimes returns
`None` — that's exactly what the type hint `-> str | None` at the top was
warning the reader to expect.

## `validate_and_crop_face(image)` — the main function

This is the one function `main.py` actually calls. Everything above it
exists just to support this.

### Preparing the image

```python
rgb_image = image.convert("RGB")
image_as_array = np.array(rgb_image)
gray_image = cv2.cvtColor(image_as_array, cv2.COLOR_RGB2GRAY)
```

`image` arrives as a PIL image object (PIL is a different image-handling
library than OpenCV, used elsewhere in the project). `.convert("RGB")`
makes sure it's definitely in standard red/green/blue color format,
regardless of whatever format it originally arrived in (some image formats
support transparency or other modes that would cause problems later).

`np.array(rgb_image)` converts that PIL image object into a numpy array —
the grid-of-numbers format OpenCV expects to work with, since PIL and
OpenCV represent images slightly differently internally even though they're
describing the same picture.

`cv2.cvtColor(image_as_array, cv2.COLOR_RGB2GRAY)` converts the color image
into grayscale. This is necessary because both the blur check and the face
detectors only look at *brightness patterns*, not color — color would just
be extra data they don't use, so simplifying to grayscale first makes
everything that follows faster and simpler.

### The quality checks run first

```python
if is_too_blurry(gray_image):
    return None, "This photo looks too blurry. Please upload a sharper, more focused photo."

brightness_error = is_bad_brightness(gray_image)
if brightness_error:
    return None, brightness_error
```

These two checks run before any face detection happens at all — there's no
point spending time looking for a face in a photo that's already unusable
for other reasons. Both checks return a pair of values using Python's
comma syntax: `None` (meaning "no usable image") paired with an error
message. This matches the type hint at the top of the function,
`tuple[Image.Image | None, str | None]` — a **tuple** is just a fixed pair
(or longer group) of values bundled together; here it's always exactly two
values: an image-or-nothing, and a message-or-nothing.

### Looking for faces

```python
faces = FACE_DETECTOR.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=6, minSize=(60, 60))
```

`detectMultiScale` is the actual face-searching function, provided by the
Haar cascade loaded earlier. It slides a small window across the entire
photo, checking over and over: "does the patch of image inside this window
right now look like a face?" Three settings control how it searches:

- **`minSize=(60, 60)`** — don't even bother checking windows smaller than
  60×60 pixels; anything smaller is too small to trust as a real face
  detection anyway.
- **`scaleFactor=1.1`** — people's faces show up at different sizes in
  different photos, depending how close to the camera they are, but the
  detector's internal patterns are a fixed size. To cope with this, the
  whole image is repeatedly shrunk by 10% and re-scanned from scratch each
  time, so faces of many different sizes still eventually get checked at a
  size the detector recognizes.
- **`minNeighbors=6`** — because the window slides across the image in
  small steps and at multiple sizes, a real face usually gets flagged
  several times in a row, at slightly different overlapping positions. This
  setting says: only trust a detection if at least 6 of these nearby,
  overlapping windows *also* agree there's a face roughly there. A random
  patch of background that only looks vaguely face-like from one exact
  angle/position almost never gets that much agreement, so this filters out
  a lot of false alarms. (Raising this number makes detection stricter but
  risks missing real faces; lowering it makes it more lenient but risks
  more false alarms.)

The result, stored in `faces`, is a list of boxes — each one describing
where a possible face was found, as four numbers: `x` and `y` (the
position of the box's top-left corner, measured in pixels from the photo's
own top-left corner) and `w` and `h` (the box's width and height).

### Double-checking with the eye detector

```python
real_faces = []
for (x, y, w, h) in faces:
    face_area = gray_image[y:y + h, x:x + w]
    eyes_in_this_face = EYE_DETECTOR.detectMultiScale(face_area, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15))
    if len(eyes_in_this_face) >= 1:
        real_faces.append((x, y, w, h))
```

Haar cascades aren't perfect — sometimes they mistake a random patch of
background clutter for a face. As a simple extra sanity check, this loop
goes through every candidate box the face detector found, and for each one,
crops out just that little rectangle of the photo
(`gray_image[y:y + h, x:x + w]` — this is Python's "slicing" syntax for
grabbing a sub-section of a grid of numbers) and runs the separate eye
detector *only within that small region*. If at least one eye is found
inside it (`len(eyes_in_this_face) >= 1` — `len()` counts how many items
are in a list), the box is trusted and added to a new list called
`real_faces` (started as an empty list, `[]`, and built up one item at a
time with `.append(...)`). Random background clutter almost never happens
to contain something eye-shaped, so this filters out most false alarms.
Requiring only *one* eye (not two) also means a face turned to the side,
showing just one eye, still correctly counts as a real face.

### Deciding what to do based on how many real faces were found

```python
if len(real_faces) > 1:
    return None, "Multiple faces detected. Please upload a photo with only your face in frame."

if len(real_faces) == 0:
    return rgb_image, None
```

**More than one face** → rejected. This app is built to analyze one
person's skin at a time, so a photo with two or more people in it doesn't
make sense to process.

**Zero faces** → accepted as-is, unchanged, with no error at all. This is a
deliberate choice, not a shortcut: looking at the actual training photos
used to build the AI model behind this app, most of the 8 skin condition
categories were trained on extreme close-up shots of a small patch of skin
(a cheek, a forehead) with no face structure visible in the photo at all —
only one category (wrinkles) used whole-face portraits. So a photo with "no
face" detected in it usually isn't a bad photo — it's most likely exactly
the kind of close-up shot the AI model is used to seeing, and should be
passed through rather than rejected.

**Exactly one face** (anything not caught by the two conditions above) →
falls through to the cropping code below.

### Cropping to the face, with padding

```python
x, y, w, h = real_faces[0]
extra_x = int(w * EXTRA_SPACE_AROUND_FACE)
extra_y = int(h * EXTRA_SPACE_AROUND_FACE)

left = max(0, x - extra_x)
top = max(0, y - extra_y)
right = min(image_as_array.shape[1], x + w + extra_x)
bottom = min(image_as_array.shape[0], y + h + extra_y)

cropped_image = rgb_image.crop((left, top, right, bottom))
return cropped_image, None
```

`real_faces[0]` grabs the one (and only, at this point) detected face box,
and unpacks its four numbers into `x`, `y`, `w`, `h`.

`extra_x`/`extra_y` calculate how much extra padding to add — 30% of the
face's own width/height (`EXTRA_SPACE_AROUND_FACE = 0.3`), converted to a
whole number of pixels with `int(...)` (since you can't have a fraction of
a pixel).

`left`/`top`/`right`/`bottom` calculate the actual crop boundaries, padded
outward from the detected face box in every direction. `max(0, ...)` and
`min(image size, ...)` are safety clamps: they make sure the padded box
never tries to reach past the left/top edge of the original photo (which
would be a negative position, not possible) or past the right/bottom edge
(which would try to read pixels that don't exist). `image_as_array.shape`
gives the dimensions of the image array — `.shape[1]` is its width in
pixels, `.shape[0]` is its height.

Finally, `rgb_image.crop((left, top, right, bottom))` performs the actual
crop on the original *color* image (not the grayscale one used for
detection — that was only ever needed to *find* the face, the real color
photo is what actually gets analyzed by the AI afterward). The result is
returned alongside `None` (meaning "no error"), matching the same two-value
pattern used everywhere else in this function.

## An honest limitation worth knowing

Because "no face detected" is now treated as a valid, accepted case rather
than a rejection, this file no longer guarantees the uploaded photo is
actually a picture of skin at all — it only checks sharpness and
brightness in that case. A photo of a wall or a screenshot with reasonable
focus and lighting would currently pass through untouched. The old "must
find a face" rule was accidentally doing double duty: verifying *both*
"this is a real face" and, loosely, "this is a real photo of a person." For
a small student project this tradeoff is a non-issue, but if this app were
ever opened up to the public, it would be worth adding some other basic
check in its place.

## A bigger, unresolved question

The notebook used to train the AI model (`dataset.ipynb`) tests the
model's accuracy directly on the original training-style photos, never
through this face-detection-and-crop process. So the accuracy numbers that
notebook reports don't fully prove how well the model performs on a real
visitor's face-cropped selfie specifically — there's a real gap between how
the model was tested and how it's actually used in the live app. This isn't
something a small code change here can fully fix, since the training photos
themselves mix two very different styles (whole-face portraits for one
category, close-up patches for the rest) — it's documented here as a known,
understood limitation of the project rather than something silently
ignored.
