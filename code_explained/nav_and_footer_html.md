# templates/_nav.html and _footer.html — explained for someone who has never written code

These are two small files, each holding one reusable piece of every page:
the navigation bar at the very top, and the footer at the very bottom.
`base.html` pulls both of them in on every single page using Jinja's
`{% include %}` instruction (see `base_html.md`).

## Why the filenames start with an underscore

`_nav.html` and `_footer.html` (note the leading `_`) is just a naming
convention — not a rule Flask enforces — that signals "this file is a small
reusable fragment, not a full page anyone would ever visit directly." You'd
never type `yoursite.com/_nav.html` into a browser; it only makes sense
when inserted inside another page.

## `_nav.html`

```html
<nav class="site-nav">
  <a href="{{ url_for('index') }}" class="logo">Tvisha <span>Skin</span></a>
  <div class="nav-links">
    <a href="{{ url_for('scanner') }}">Skin Scanner</a>
    <a href="{{ url_for('about') }}">About</a>
  </div>
</nav>
```

- `<nav class="site-nav">` — `<nav>` is an HTML tag that specifically means
  "this section contains navigation links," which helps browsers, search
  engines, and accessibility tools understand the page's structure, on top
  of it just being a normal container. `class="site-nav"` attaches a name
  that `app.css` uses to actually style how this looks (the styling itself
  lives in `app.css`, not here — see `app_css.md`).
- `<a href="{{ url_for('index') }}" class="logo">Tvisha <span>Skin</span></a>`
  — an `<a>` tag is a link; clicking it navigates the browser somewhere
  else. `href` is the destination. Instead of hardcoding the address (like
  `href="/"`), `{{ url_for('index') }}` asks Flask to look up whatever
  address is currently assigned to the function named `index` in
  `main.py` (which happens to be `/`, the home page). If that address were
  ever changed in `main.py`, this link would automatically still work,
  without needing to be updated here too. The text inside the link,
  `Tvisha <span>Skin</span>`, is the visible logo text — wrapping just the
  word "Skin" in its own `<span>` tag lets `app.css` style that one word
  slightly differently (in italics, in a different color) from the rest.
- The two links inside `<div class="nav-links">` work exactly the same way,
  pointing at the `scanner` and `about` routes respectively.

## `_footer.html`

```html
<footer class="site-footer">
  <div class="footer-inner">
    <span class="footer-logo">TVISHA</span>
    <span class="footer-copy">© 2026 Tvisha Skincare. All rights reserved.</span>
    <div class="footer-social">
      <a href="#" class="social-pill" aria-label="Instagram">IG</a>
      <a href="#" class="social-pill" aria-label="Facebook">FB</a>
      <a href="#" class="social-pill" aria-label="TikTok">TT</a>
    </div>
  </div>
</footer>
```

- `<footer>` is another semantic HTML tag (like `<nav>`) — it specifically
  marks "this is the footer of the page," again mostly useful for
  accessibility and search engines, beyond just being a styled box.
- The wordmark, the copyright line, and three small round "social media"
  buttons are shown, in plain text — nothing dynamic here, no Jinja values
  needed, since none of this content changes based on data.
- `href="#"` on each social link is a placeholder — a `#` link doesn't
  actually go anywhere; it's commonly used as a stand-in when a real
  destination isn't set up yet. These are decorative for now, not wired up
  to actual Instagram/Facebook/TikTok accounts.
- `aria-label="Instagram"` (and similarly for Facebook/TikTok) is an
  accessibility attribute — since the visible text on these buttons is just
  "IG"/"FB"/"TT," `aria-label` gives screen-reading software a clearer
  full word to announce instead, for visitors who can't see the abbreviated
  text on screen.
