# templates/login.html — explained for someone who has never written code

The login form. Extends `base.html`, same pattern as every other page.

```html
{% extends "base.html" %}
{% block title %}Log In - TVISHA{% endblock %}
{% block content %}
```
Standard inheritance, as covered in `base_html.md`.

## The form

```html
<form method="POST" action="/login">
  <div class="mb-3">
    <label for="username" class="form-label">Username</label>
    <input type="text" class="form-control" id="username" name="username" required>
  </div>
  <div class="mb-3">
    <label for="password" class="form-label">Password</label>
    <input type="password" class="form-control" id="password" name="password" required>
  </div>
  <button type="submit" class="btn btn-primary w-100">Log In</button>
</form>
```
- `method="POST" action="/login"` — submits to `main.py`'s `login()` route,
  same request/response cycle explained in `main.md` for the upload form.
- `name="username"` / `name="password"` — these exact strings are what
  `main.py` reads with `request.form.get("username", ...)` and
  `request.form.get("password", "")`. If these names didn't match exactly,
  the server would receive the submission but find nothing under those
  keys.
- `type="password"` on the password field is what makes the browser mask
  the typed characters as dots/asterisks on screen — a purely visual/UX
  behavior; it doesn't change how the data is actually sent to the server.
- `required` is a basic browser-side check (won't let the form submit if
  empty) — purely a convenience, not real security. The actual check that
  matters happens in `main.py`/`auth.py` on the server, since a browser-side
  `required` attribute is trivial to bypass (e.g. by submitting the form
  with a tool other than a browser).
- `class="form-control"`, `class="btn btn-primary"` etc. are Bootstrap's
  ready-made styling classes (Bootstrap is loaded via CDN in `base.html`)
  — no custom CSS was needed for this page.

## What happens after submitting

Handled entirely in `main.py`'s `login()` route (see `main.md`): it calls
`auth.py`'s `verify_user()`, and either flashes an error and reloads this
same page, or sets the session and redirects to the home page.

## The flash messages

Notice this file itself has no code to display error messages (like
"Invalid username or password") — that's because `base.html` now has a
single, shared flash-message block that every page automatically includes
(see `base_html.md`), so `login.html` doesn't need its own copy.
