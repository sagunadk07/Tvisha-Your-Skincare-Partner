# static/js/scanner.js — explained for someone who has never written code

## What JavaScript is, and why it's different from Python/HTML/CSS

HTML describes structure, CSS describes appearance, and Python (in
`main.py` and the other `.py` files) runs on the *server* — the computer
hosting the website — before a page is ever sent to a visitor. JavaScript
is different: it's a programming language that runs directly inside the
visitor's own web browser, *after* the page has already loaded, and it can
react instantly to things the visitor does (clicking, typing, dragging)
without needing to ask the server anything. This file is what makes the
upload page feel interactive rather than static — showing a live preview,
supporting drag-and-drop, and showing a spinner — all without ever
reloading the page.

## How this file gets connected to the page

`scanner.html` loads this exact file with
`<script src="{{ url_for('static', filename='js/scanner.js') }}"></script>`,
placed near the very end of the page (see `scanner_html.md`). The browser
downloads this file and runs it top to bottom, once, right when the page
finishes loading.

## Grabbing references to page elements

```js
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const previewWrap = document.getElementById('preview-wrap');
const previewImg = document.getElementById('preview-img');
const removeBtn = document.getElementById('remove-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const form = document.getElementById('upload-form');
```

`document` is a built-in object every browser provides, representing the
entire current web page. `document.getElementById('some-id')` searches the
whole page for the one element that has that exact `id` attribute (ids are
meant to be unique — no two elements on the same page should share one) and
returns it, so JavaScript can then read or change it.

`const` declares a variable whose value won't be reassigned later (as
opposed to `let`, used for a value that will change — see `dragging` and
`hintHidden` further down, and in `result.js`). Each line here just stores
a reference to one specific element from `scanner.html`, by matching the
exact `id` strings written in that file. If any of these ids were ever
renamed in the HTML without updating this file to match, the corresponding
line here would return `null` (JavaScript's version of "nothing found"),
and any code trying to use it afterward would break — the two files are
tightly linked together through these exact id names.

## Reacting to a normal file selection

```js
fileInput.addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) showPreview(file);
});
```

`.addEventListener('change', ...)` registers a function to run automatically
whenever a `'change'` event happens on `fileInput` — for a file input
specifically, this event fires the moment the visitor finishes picking a
file through the normal file-browser dialog.

`e => { ... }` is an **arrow function** — a compact way of writing a small,
often-throwaway function in JavaScript, roughly equivalent to Python's
smaller function syntax. `e` (short for "event") is automatically passed in
by the browser, holding details about what just happened. `e.target` is the
specific element the event happened on (`fileInput` itself, in this case);
`.files` is always a list of files (even when only one was selected), so
`[0]` grabs that one file. `if (file) showPreview(file);` only calls the
`showPreview` function (defined further down) if a file actually exists —
this guards against the rare case where the change event fires but no file
ended up being selected.

## Drag-and-drop support

```js
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; showPreview(file); }
});
```

Three separate events work together to support dragging a file from the
desktop directly onto the page:

- **`'dragover'`** fires continuously while something is being dragged over
  the drop zone. `e.preventDefault()` is essential here — without it, the
  browser's own default behavior (usually just opening the dragged file in
  a new tab) would take over instead of letting this custom handling run.
  `dropZone.classList.add('dragover')` adds a CSS class named `dragover` to
  the element, which is what makes the drop zone visually highlight (a
  different border color/background) while something is hovering over it
  — that visual effect itself is defined in `scanner.html`'s CSS, using the
  `.drop-zone.dragover` selector; this line of JavaScript is only
  responsible for adding/removing that class at the right moments.
- **`'dragleave'`** fires when the dragged item moves back off the drop
  zone without being dropped — this removes the highlight again.
- **`'drop'`** fires when the file is actually released over the drop zone.
  `e.dataTransfer.files` holds whatever file(s) were dropped, the same
  shape as `fileInput.files` from before. The line
  `fileInput.files = e.dataTransfer.files` manually assigns the dropped
  file(s) into the actual file input element — this keeps the *real*
  underlying form input in sync with what was dragged in, which matters
  because it's the file input's contents that actually get sent to the
  server when the form is eventually submitted, not anything about how the
  file visually arrived on the page.

## `showPreview(file)` — a regular named function

```js
function showPreview(file) {
  const reader = new FileReader();
  reader.onload = e => {
    previewImg.src = e.target.result;
    previewWrap.style.display = 'block';
    dropZone.style.display = 'none';
  };
  reader.readAsDataURL(file);
}
```

Unlike the short arrow functions used directly inside `addEventListener(...)`
calls above, this is a full, named function — written this way because it's
called from two different places (both the normal file-picker path and the
drag-and-drop path), so writing it once and reusing it avoids duplicating
the same logic twice.

`new FileReader()` creates a browser tool specifically for reading the
contents of files the visitor has selected, without uploading them
anywhere yet. `reader.onload = e => { ... }` sets up a function to run
automatically once the reading finishes (reading a file, even a small one,
technically takes a small amount of time, so this can't just happen
instantly on the very next line — JavaScript handles this kind of
"wait for something, then react" pattern constantly). Once loaded,
`e.target.result` holds the file's contents converted into a **data URI** —
the same kind of "image data embedded directly inside a text string"
concept explained in `main.md` for `preview_uri`. Setting `previewImg.src`
to that value makes the browser immediately display the chosen photo,
without it ever having been uploaded to the server at this point — this
preview is happening entirely inside the visitor's own browser.

`previewWrap.style.display = 'block'` and `dropZone.style.display = 'none'`
directly change those elements' CSS `display` property from JavaScript,
which is how the preview box is shown and the (now redundant) drop zone is
hidden the moment a file is selected.

`reader.readAsDataURL(file)` is the line that actually kicks off the whole
reading process described above — everything before it in this function was
just *preparing* what should happen once reading finishes.

## Removing the selected file

```js
removeBtn.addEventListener('click', () => {
  fileInput.value = '';
  previewWrap.style.display = 'none';
  dropZone.style.display = 'block';
});
```

When the small "✕" button is clicked, `fileInput.value = ''` clears
whatever file was selected (an unusual-looking but standard way to reset a
file input in JavaScript — file inputs can't be cleared by simply setting
`.files` to an empty value directly, for browser security reasons).
`previewWrap`/`dropZone`'s visibility is then flipped back to how it was
originally, so the visitor can pick a different photo.

## Showing the spinner on submit

```js
form.addEventListener('submit', () => {
  analyzeBtn.disabled = true;
  analyzeBtn.querySelector('.default-state').style.display = 'none';
  analyzeBtn.querySelector('.analyzing-state').style.display = 'flex';
});
```

This runs right when the whole form is actually submitted (the visitor
clicked "Analyze Skin," and the browser is now sending the photo to the
server). `analyzeBtn.disabled = true` disables the button — preventing the
visitor from accidentally clicking it a second time while the first request
is still processing, which could otherwise trigger two uploads at once.

`analyzeBtn.querySelector('.default-state')` searches, but only *within*
`analyzeBtn` itself (rather than the whole page), for the first element
matching the CSS selector `.default-state` — recall from `scanner_html.md`
that the button contains two alternate inner `<span>`s, one for its normal
text and one for the spinner, only one of which is meant to be visible at a
time. This line hides the normal text and shows the spinner instead,
giving the visitor visual confirmation that the page is actively working on
their upload rather than appearing frozen — a small but important detail,
since face detection and the AI prediction together take a moment to
complete on the server.
