# templates/index.html — explained for someone who has never written code

The home page. Extends `base.html` (read `base_html.md` first). This page
is also where the actual photo upload happens — there is no separate
"scanner" page in this design; everything lives on `/`.

```html
{% extends "base.html" %}
{% block title %}Home - TVISHA{% endblock %}
{% block content %}
```
Standard inheritance, as covered in `base_html.md`.

## Hero section

```html
<section class="hero-section">
  <div class="container">
    <div class="hero-content">
      <div class="hero-text">
        <span class="hero-tag">AI Powered Skin Analysis</span>
        <h1>Discover Healthier Skin with <span>TVISHA</span></h1>
        <p>Upload a clear image of your skin and receive AI-powered
        skin condition analysis along with personalized skincare
        recommendations.</p>
        <a href="#upload" class="hero-btn">Analyze Your Skin</a>
      </div>
      <div class="hero-image">
        <div class="hero-placeholder">Hero Image</div>
      </div>
    </div>
  </div>
</section>
```
Just a headline, description, and a button. `href="#upload"` is an anchor
link — clicking it scrolls down to the section below with `id="upload"`,
rather than navigating to a different page. `.hero-placeholder` is a plain
gray box standing in for a real image that hasn't been added yet.

## Upload section — the actual scanner, gated by login

```html
<section class="upload-section" id="upload">
  <div class="container">
    <h2>Upload Your Skin Photo</h2>
    <p class="upload-subtitle">Use a clear, well-lit photo for the most accurate analysis.</p>

    {% if session.user_id %}
    <form action="/analyze" method="POST" enctype="multipart/form-data" id="uploadForm">
      <div class="upload-box" id="uploadBox">
        <input type="file" id="fileInput" name="skin_image" accept="image/*" hidden>
        <div class="upload-placeholder" id="uploadPlaceholder">
          <i class="bi bi-cloud-upload upload-icon"></i>
          <p>Drag & drop your photo here, or <span class="browse-text">click to browse</span></p>
        </div>
        <img id="previewImage" class="preview-image" hidden>
      </div>
      <button type="submit" id="analyzeBtn" class="analyze-btn" disabled>Analyze Skin</button>
      <div id="loadingState" class="loading-state" hidden>
        <div class="spinner"></div>
        <p>Analyzing your skin...</p>
      </div>
    </form>
    {% else %}
    <div class="login-prompt">
      <p>You need an account to analyze your skin.</p>
      <a href="/login" class="analyze-btn">Log In to Continue</a>
      <p class="upload-subtitle">New here? <a href="/signup">Create one — it only takes a minute</a></p>
    </div>
    {% endif %}
  </div>
</section>
```

This is the most important part of this page. `{% if session.user_id %} ... {% else %} ... {% endif %}`
decides which of two completely different things a visitor sees, based on
whether they're logged in (same `session` object explained in
`base_html.md`).

**If logged in** — the real upload form renders:
- `action="/analyze" method="POST" enctype="multipart/form-data"` — submits
  to `main.py`'s `analyze()` route. `enctype="multipart/form-data"` is
  required specifically because a file is being uploaded.
- `<input type="file" id="fileInput" name="skin_image" ... hidden>` — the
  real, functional file picker, made invisible (`hidden`) and stretched
  over the decorative `upload-box` div via CSS, so the whole styled box
  looks clickable/droppable even though this plain input is the actual
  interactive element. `name="skin_image"` must exactly match what
  `main.py` reads with `request.files.get("skin_image")`.
  `accept="image/*"` hints to the browser's file picker to filter for
  image files (a convenience only — `main.py` independently re-checks the
  file extension server-side, since browser-side filtering is trivial to
  bypass).
- The `upload-placeholder` and `previewImage` elements are two states of
  the same spot — one shown before a file is picked, one after — swapped
  by `static/js/main.js` (see that file's own explanation).
- The button starts `disabled` and `main.js` enables it once a valid image
  file has actually been chosen.
- `loadingState` (spinner + text) starts hidden and is revealed by
  `main.js` right as the form is actually submitted.

**If logged out** — none of that renders at all. Instead, a short message
and two links (`/login`, `/signup`) are shown. This matters for a real
reason, not just cosmetics: `main.py`'s `analyze()` route independently
rejects any submission from someone who isn't logged in (see `main.md`'s
explanation of the `"user_id" not in session` check), so showing the real
form to a logged-out visitor would let them fill out the whole thing and
pick a photo, only to be told "please log in" *after* clicking submit.
Hiding the form and showing a clear prompt instead means a logged-out
visitor understands what's needed *before* they try, not after.

## How It Works / Skin Conditions sections

```html
<section class="how-it-works" id="how-it-works">
  ...
  <div class="step">
    <span class="step-number">01</span>
    <h3>Upload Photo</h3>
    <p>Take a clear photo of your skin in good lighting.</p>
  </div>
  ...
</section>

<section class="conditions" id="conditions">
  ...
  <div class="condition-cards">
    <div class="condition-card">Redness</div>
    <div class="condition-card">Dark Spots</div>
    ...
  </div>
</section>
```
Two more purely informational sections, linked from the nav bar's anchor
links (`#how-it-works`, `#conditions`). The 8 condition names here are
written out by hand rather than looped from `CLASS_NAMES` (unlike
`about.html`'s equivalent grid) — a stylistic difference from how the
About page does the same thing, not a bug, just a different author's
choice for this particular section.

No `extra_js` block — this page relies entirely on the shared `main.js`
loaded by `base.html`, with nothing extra of its own.
