# templates/scanner.html — explained for someone who has never written code

The upload page — where a visitor actually picks a photo and submits it.
This is the first template covered so far that includes a real HTML
**form**, and the first that loads its own JavaScript file.

## Flash messages — showing errors from the previous attempt

```html
{% with messages = get_flashed_messages() %}
  {% if messages %}
    {% for message in messages %}
      <div class="flash">{{ message }}</div>
    {% endfor %}
  {% endif %}
{% endwith %}
```

Recall from `main.md` that when something goes wrong with an uploaded photo
(wrong file type, too blurry, no face, etc.), `main.py` calls `flash("some message")`
and then redirects the visitor back to this page. This block of Jinja code
is what actually *displays* that message when the visitor lands back here.

- `{% with messages = get_flashed_messages() %}` — `get_flashed_messages()`
  is a function Flask provides specifically for this purpose: it returns a
  list of any pending flashed messages, and — importantly — clears them out
  once read, so the same message doesn't keep reappearing on future page
  visits. `{% with ... %}` is Jinja's way of creating a short-lived local
  variable (here, `messages`) that only exists for the duration of this
  block.
- `{% if messages %}` — an **if statement** in Jinja works the same way it
  does in Python: only run what's inside it if the condition is true. Here,
  an empty list counts as "false," so this whole block is simply skipped if
  there are no messages to show.
- `{% for message in messages %}` — loops over every message (usually
  there's just one, but the code handles any number correctly), wrapping
  each one in a `<div class="flash">` so `app.css`'s `.flash` styling
  (a soft pink error box) applies to it.

## The upload form itself

```html
<form action="{{ url_for('analyze') }}" method="POST" enctype="multipart/form-data" id="upload-form">
```

A `<form>` tag groups together a set of inputs that get sent to the server
together, all at once, when submitted.

- `action="{{ url_for('analyze') }}"` — where the form's data gets sent when
  submitted: the `/analyze` route in `main.py`.
- `method="POST"` — the way the data is sent. `POST` is the standard method
  for submitting a form (as opposed to `GET`, generally used just for
  requesting a page to *view*, not for sending data that changes something
  or performs an action). This must match the `methods=["POST"]` setting on
  the `/analyze` route in `main.py`, or the submission would fail.
- `enctype="multipart/form-data"` — this setting is *required* specifically
  because this form includes a file upload. Without it, the browser
  wouldn't properly package and send the actual contents of the selected
  file along with the rest of the form.
- `id="file-input"` (and the other `id="..."` attributes throughout this
  file) — an `id` is a unique label attached to one specific element, used
  so that CSS or JavaScript can find and target that exact element. See
  `scanner_js.md` for how `scanner.js` uses several of these ids.

### The drop zone

```html
<div class="drop-zone" id="drop-zone">
  <input type="file" name="skin_image" id="file-input" accept=".png,.jpg,.jpeg,.webp" />
  <span class="drop-icon">🌸</span>
  <span class="drop-label">Drop your image here</span>
  <span class="drop-hint">PNG, JPG, JPEG, WEBP · Max 10MB</span>
</div>
```

`<input type="file" ...>` is the actual, real file-picker element — clicking
it opens the operating system's normal file browser dialog. It's made
invisible and stretched to cover the entire drop zone box via CSS (see
`app_css.md`/the page's own `extra_style` block), so visually, the whole
decorated box (icon, "Drop your image here" text, file-type hint) looks
like the interactive element, even though the real clickable/droppable part
is this invisible input sitting on top of it.

- `name="skin_image"` — this exact name is what `main.py` looks for with
  `request.files.get("skin_image")`. If this name were changed here without
  also updating `main.py`, file uploads would silently stop working, since
  the server would be looking for a name that no longer exists.
- `accept=".png,.jpg,.jpeg,.webp"` — a hint to the browser's own file
  picker, filtering what's easy to select in that dialog window. This is
  only a convenience for the visitor — it doesn't actually prevent other
  file types from being selected or uploaded through other means, which is
  exactly why `main.py` independently re-checks the file extension itself
  once the upload actually arrives on the server (never trust checks done
  only in the browser, since they're easy to bypass).

### The preview

```html
<div id="preview-wrap">
  <img id="preview-img" src="" alt="Preview" />
  <button type="button" class="remove-btn" id="remove-btn">✕</button>
</div>
```

Initially hidden (via CSS — `#preview-wrap { display: none; }`), this box is
shown by `scanner.js` once a photo has been chosen, displaying a preview of
it along with a small "✕" button to remove the selection and start over.
`<img id="preview-img" src="" alt="Preview" />` starts with an empty `src`
(no image loaded yet) — `scanner.js` is what actually fills that in once a
file is picked (see `scanner_js.md`).

### The submit button

```html
<button type="submit" class="btn btn-dark analyze-btn" id="analyze-btn">
  <span class="default-state">Analyze Skin</span>
  <span class="analyzing-state">
    <span class="spinner"></span> Analyzing…
  </span>
</button>
```

`type="submit"` makes this button, when clicked, actually submit the whole
`<form>` it's inside. It visually contains two alternate states stacked on
top of each other — `default-state` (plain text) and `analyzing-state` (a
spinning loading icon plus "Analyzing…" text) — only one of which is shown
at a time, controlled by CSS initially and then swapped by `scanner.js`
right when the form is submitted, to give the visitor visual feedback that
something is actually happening while the server processes their photo.

## The JavaScript

```html
{% block extra_script %}
<script src="{{ url_for('static', filename='js/scanner.js') }}"></script>
{% endblock %}
```

Loads `static/js/scanner.js`, which is what actually makes the drag-and-drop,
preview, and spinner behavior described above work. See `scanner_js.md` for
the full breakdown of that file.
