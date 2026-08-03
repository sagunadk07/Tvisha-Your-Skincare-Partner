# templates/base.html — explained for someone who has never written code

## What HTML even is

HTML (HyperText Markup Language) is not a programming language in the sense
that Python is — it doesn't do calculations or make decisions on its own.
It's a **markup language**: plain text with special tags (words wrapped in
angle brackets, like `<p>` and `</p>`) that describe the *structure* of a
page — "this is a paragraph," "this is a heading," "this is a link." A web
browser reads this structure and draws it on screen accordingly. Most tags
come in pairs: an opening tag (`<p>`) and a matching closing tag (`</p>`),
with the actual content sandwiched between them.

## What Jinja is

Flask uses a templating system called **Jinja** to let HTML files contain
small bits of logic and dynamic data, not just fixed text. Anything wrapped
in `{% ... %}` is a Jinja *instruction* (like a loop, or "extend this other
file"). Anything wrapped in `{{ ... }}` is a Jinja *value* — it gets
replaced with the actual data at the moment the page is built, right before
being sent to the visitor's browser. None of this Jinja syntax is sent to
the browser itself — by the time the page reaches a visitor, it's plain
ordinary HTML; the `{% %}`/`{{ }}` parts have already been processed and
replaced on the server.

## What this particular file is for

Every page on this site needs the same basic skeleton: a `<head>` linking
fonts/Bootstrap/the stylesheet, the navigation bar, and (at the very
bottom) the shared JavaScript file. Without this file, that skeleton would
have to be copied and pasted into every single page. `base.html` defines
that skeleton exactly once — other pages **extend** it and only supply the
part that's actually different about them. This is called **template
inheritance**.

## The `<head>`

```html
<title>{% block title %}TVISHA{% endblock %}</title>
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
<!-- Bootstrap -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<!-- Bootstrap Icons -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<!-- CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
{% block extra_css %}{% endblock %}
```
- `{% block title %}TVISHA{% endblock %}` — a **Jinja block**, a named
  placeholder. This file provides a default title, but any page extending
  it can override just this piece.
- The Google Fonts and Bootstrap/Bootstrap Icons `<link>` tags load
  ready-made styling and icon libraries directly from the internet (a
  **CDN** — Content Delivery Network — a fast, shared hosting service for
  common files like this), rather than this project having to write all
  that CSS/icon artwork itself.
- `<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">`
  loads this project's *own* stylesheet, on top of Bootstrap.
  `url_for('static', filename='css/style.css')` is Flask working out the
  correct address for a file sitting in the `static/` folder, rather than
  that address being typed by hand.
- `{% block extra_css %}{% endblock %}` — an empty placeholder for any
  extra, page-specific CSS a particular page might want to add.

## The navigation bar

```html
<nav class="navbar">
<div class="container">
<a href="/" class="logo">TVISHA<span>Skin</span></a>
<ul class="nav-links">
<li><a href="/">Home</a></li>
<li><a href="#how-it-works">How It Works</a></li>
<li><a href="#conditions">Skin Conditions</a></li>
<li><a href="/about">About</a></li>
{% if session.user_id %}
{% if session.is_admin %}
<li><a href="/admin">Admin</a></li>
{% endif %}
<li><a href="/logout">Logout ({{ session.username }})</a></li>
{% else %}
<li><a href="/login">Login</a></li>
<li><a href="/signup">Sign Up</a></li>
{% endif %}
</ul>
<a href="#upload" class="nav-btn">Analyze Skin</a>
</div>
</nav>
```
Unlike some earlier versions of this project, the nav bar here is written
directly inside `base.html` itself, rather than pulled in from a separate
file — either approach is valid; this one just keeps everything about the
overall page frame in one place.

`href="#how-it-works"` and `href="#conditions"` are **anchor links** — the
`#` means "jump to the element on *this same page* whose `id` matches the
text after it" (e.g. `id="how-it-works"` on a section in `index.html`),
rather than navigating to a different page entirely. This only works
correctly from the home page, since that's the only page with those
section ids.

The `{% if session.user_id %} ... {% else %} ... {% endif %}` block is
what makes the nav show different links depending on whether someone is
logged in. `session` is a special object Flask automatically makes
available inside every Jinja template — no route needs to explicitly pass
it in. `session.user_id` reads the same key that `main.py` sets during
login/signup (see `main.md`); if it's missing (nobody logged in), Jinja
treats that as "false-y" and the `{% else %}` branch runs instead, showing
Login/Sign Up links. If it's present, `{{ session.username }}` displays the
actual logged-in username right in the nav.

**The nested `{% if session.is_admin %}` inside that** only shows an
"Admin" link when the logged-in visitor's session also has `is_admin` set
to true (see `main.md`'s explanation of where that gets set, during
signup/login). It's deliberately placed *inside* the `session.user_id`
check rather than as its own separate top-level condition — an admin is
always also a logged-in user, so nesting it here means the code never
needs to check "is this visitor an admin" without already having
confirmed they're logged in at all. This link is purely a convenience,
not a security boundary on its own — the real protection is the
server-side check inside `main.py`'s `/admin` route itself, which would
reject a non-admin visitor even if they somehow guessed the URL directly
without ever seeing this link.

## The flash-message block

```html
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <div class="container">
      {% for message in messages %}
        <div class="alert alert-warning mt-3">{{ message }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```
Recall from `main.md` that routes like `login()`/`signup()`/`analyze()` call
`flash("some message")` before redirecting somewhere. `get_flashed_messages()`
retrieves any pending messages (and clears them, so each one shows exactly
once). Since this block lives in `base.html`, *every* page automatically
gets this behavior — a login error, a logout confirmation, an upload
rejection, all show up the same way, no matter which page you land on
afterward. `alert`/`alert-warning` are ready-made Bootstrap classes for
styling a message box; no custom CSS was needed for this.

## The rest of the body

```html
{% block content %}
{% endblock %}
<!-- JavaScript -->
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
{% block extra_js %}{% endblock %}
```
- `{% block content %}{% endblock %}` — the main placeholder every page
  extending this file must fill in with its own visible content.
- `<script src="...js/main.js">` loads the shared JavaScript file at the
  very end of the page — standard practice, so the rest of the page's
  content loads and appears first, before the browser spends time running
  scripts. `main.js` is written defensively (see its own explanation) so it
  doesn't break on pages that don't have the specific elements it looks for.
- `{% block extra_js %}{% endblock %}` — an empty placeholder for any extra
  JavaScript a specific page might want to add on top of `main.js`.

## How a page actually uses this file

A page starts with `{% extends "base.html" %}`, then only defines whichever
of the four named blocks it actually needs (`title`, `extra_css`, `content`,
`extra_js`) — anything left undefined just falls back to this file's plain
defaults.
