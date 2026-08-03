# static/js/main.js — explained for someone who has never written code

Loaded on **every page** (referenced unconditionally near the bottom of
`base.html`). Drives the upload box on the home page: picking/dragging a
photo, showing a preview, and revealing the loading spinner right before
the real form submission happens.

## The guard around everything

```javascript
const uploadForm = document.getElementById('uploadForm');

if (uploadForm) {
  ...
}
```
`document.getElementById('uploadForm')` searches the current page for an
element with `id="uploadForm"`. Since this script runs on *every* page, but
the upload form only actually exists in `index.html`, **and only when the
visitor is logged in** (see `index_html.md`'s explanation of the
`{% if session.user_id %}` block), this element is sometimes simply not on
the page at all — in which case `getElementById` returns `null`.

Without this `if (uploadForm)` guard, every line inside would run
unconditionally, and something like `uploadBox.addEventListener(...)` would
try to call a function on `null` — which immediately crashes the whole
script with an error, on every page that doesn't have this form (`about.html`,
`login.html`, `signup.html`, and `index.html` itself for a logged-out
visitor). Wrapping everything in this one check means: only try to wire up
the upload box's behavior if it's actually present on this particular page
right now.

## Grabbing the elements

```javascript
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const previewImage = document.getElementById('previewImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
```
Each of these grabs one specific element from `index.html`, matched by its
exact `id`. These are only reached at all once the `if (uploadForm)` guard
above has already confirmed the form (and therefore all these elements
inside it) genuinely exist on the page.

## Selecting a file, and drag-and-drop

```javascript
uploadBox.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
  handleFile(e.target.files[0]);
});

uploadBox.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadBox.classList.add('drag-over');
});

uploadBox.addEventListener('dragleave', () => {
  uploadBox.classList.remove('drag-over');
});

uploadBox.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadBox.classList.remove('drag-over');
  handleFile(e.dataTransfer.files[0]);
});
```
- The real `<input type="file">` is hidden via CSS; clicking anywhere on
  the visible styled box (`uploadBox`) instead programmatically clicks the
  hidden input (`fileInput.click()`), which opens the normal system file
  picker.
- `'change'` fires once a file is actually chosen through that picker.
- The three `'dragover'`/`'dragleave'`/`'drop'` listeners implement
  drag-and-drop: `e.preventDefault()` is required on `dragover`/`drop`,
  since the browser's default behavior otherwise would try to open the
  dropped file in a new tab instead of letting this code handle it.
  `classList.add('drag-over')`/`remove('drag-over')` toggle a CSS class
  used purely for the visual highlight while something is being dragged
  over the box.
- `e.target.files[0]` (file picker) and `e.dataTransfer.files[0]` (drag-and-
  drop) are two different browser APIs for "what file did the user just
  give me," depending on how they gave it — both end up calling the same
  `handleFile` function either way.

## `handleFile(file)`

```javascript
function handleFile(file) {
  if (!file || !file.type.startsWith('image/')) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImage.src = e.target.result;
    previewImage.hidden = false;
    uploadPlaceholder.hidden = true;
  };
  reader.readAsDataURL(file);

  analyzeBtn.disabled = false;
}
```
`if (!file || !file.type.startsWith('image/')) return;` — bails out early
if nothing was actually given, or if what was given isn't an image (e.g.
someone drags in a `.pdf`) — `file.type` is a string like `"image/png"`
that the browser detects automatically.

`FileReader` is a built-in browser tool for reading the contents of a
locally-selected file. `reader.readAsDataURL(file)` reads the photo and
converts it into a **data URI** — a long text string that directly encodes
the image data, which an `<img>` tag can display straight away without
uploading anything to a server first. `reader.onload = ...` sets up what
happens once that reading finishes (it isn't instant, so this is set up in
advance): the preview `<img>`'s `src` is set to that data URI, it's made
visible, and the "drag and drop here" placeholder is hidden instead.

`analyzeBtn.disabled = false` re-enables the submit button, which starts
disabled in the HTML until a valid photo has actually been chosen.

## Submitting

```javascript
uploadForm.addEventListener('submit', () => {
  loadingState.hidden = false;
  analyzeBtn.disabled = true;
});
```
Fires the moment the form is genuinely submitted (the browser is about to
send the photo to `/analyze` and navigate to whatever page comes back).
Shows the spinner and disables the button — mainly so a visitor doesn't
click "Analyze Skin" a second time while the first request is still being
processed (face detection plus the AI prediction takes a moment). Notice
this code does **not** need to hide the spinner again or reset anything
afterward — the whole page is about to be replaced by the results page (or
a redirect back with an error), so there's nothing left to clean up here.
