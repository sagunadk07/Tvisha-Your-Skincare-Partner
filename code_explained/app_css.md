# static/css/app.css — explained for someone who has never written code

## What CSS is

If HTML is the *structure* of a page (this is a heading, this is a
paragraph, this is a button), CSS (Cascading Style Sheets) is what controls
how that structure actually *looks*: colors, spacing, fonts, sizes,
positioning, what happens on hover. Without any CSS at all, a web page
would still work — all the text and buttons would still be there and
clickable — but it would look like a plain, unstyled document from decades
ago, with black text on a white background and no real layout.

CSS is written as a series of **rules**. Each rule has a **selector**
(which elements does this rule apply to?) followed by curly braces
containing **declarations** (which properties get changed, and to what
value?), like this:

```css
.pill {
  border-radius: 20px;
  color: var(--muted);
}
```

Here, `.pill` is the selector — it means "every HTML element with
`class="pill"` on it." Everything inside the `{ }` is applied to all of
them: `border-radius: 20px;` rounds the corners, `color: var(--muted);`
sets the text color.

This file is loaded once, by `base.html`, and applies to every single page
on the site — it holds only the styling that's genuinely shared across
multiple pages. Anything specific to just one page lives in that page's own
`extra_style` block instead (see the other `_html.md` files).

## CSS variables (custom properties)

```css
:root {
  --cream:  #f9f4ee;
  --rose:   #c4836a;
  --deep:   #3a2419;
  --muted:  #8a6a5a;
  ...
  --r:      12px;
  --r-lg:   20px;
}
```

`:root` is a special selector meaning "the very top of the whole page" —
rules written here effectively apply everywhere. Anything starting with two
dashes, like `--rose`, defines a **CSS variable**: a named value that can be
reused anywhere else in the file by writing `var(--rose)` instead of typing
the raw value again. `#c4836a` is a **hex color code** — a way of writing
an exact color using six characters, where every two characters describe
how much red, green, and blue light to mix together respectively.

Defining the whole color palette (and a couple of reusable sizes, `--r`/`--r-lg`
for rounded corners) once, at the top, and then referring back to those
names everywhere else in the file, means the entire site's look can be
adjusted by changing a value in exactly one place — instead of having to
hunt down and update the same raw color code copy-pasted throughout dozens
of different rules.

## Global resets

```css
* , *::before, *::after { box-sizing: border-box; }

body {
  font-family: 'DM Sans', sans-serif;
  background: var(--cream);
  color: var(--deep);
  margin: 0;
}
```

`*` is the **universal selector** — it matches literally every single
element on the page. `box-sizing: border-box` changes a fairly technical
default about how an element's width/height are calculated when it also has
padding and a border, in a way that makes sizing elements far more
predictable and is used almost universally in modern web design.

`body` styles the whole visible page: sets the default font to a typeface
called "DM Sans" (falling back to the browser's generic `sans-serif` font if
that specific one somehow fails to load), the background color, the default
text color, and removes the small default margin browsers normally add
around the very edge of a page.

## Reusable components

The rest of the file defines a handful of small, reusable visual
"components" — patterns used repeatedly throughout the site:

- **`.eyebrow`** — the small uppercase label style seen above several
  headings ("Powered by EfficientNet-B0," "About Tvisha"), with a short
  horizontal line before it created using `::before` (a way of inserting a
  small extra decorative element via CSS alone, without needing an actual
  extra HTML tag for it).
- **`.pill`** and its color variants (`.pill--rose`, `.pill--green`,
  `.pill--amber`, `.pill--coral`) — the small rounded tag/badge shape used
  for condition names, ingredients, and confidence-level indicators. The
  base `.pill` class sets the shared shape and sizing; each `--color`
  variant only needs to override the background/text/border colors on top
  of that shared base.
- **`.btn`**, `.btn-dark`, `.btn-outline`, `.btn-sm` — the button styles.
  `.btn` alone defines the shared shape (rounded, padded, uppercase text);
  `.btn-dark` and `.btn-outline` are two different color treatments layered
  on top of it, and `.btn-sm` is a smaller size variant, usable in
  combination with either color.
- **`.site-nav`, `.logo`, `.nav-links`** — styling for `_nav.html`.
- **`.site-footer`, `.footer-inner`, `.social-pill`** — styling for
  `_footer.html`.
- **`.card`, `.card--hover`** — the white, rounded-corner, subtly-shadowed
  box shape used all over the site (feature boxes, score cards,
  recommendation cards). `.card--hover` is an optional add-on that makes a
  card lift slightly and gain a stronger shadow when the mouse hovers over
  it — used only on cards that are meant to feel interactive/clickable.
- **`.flash`** — the pale pink error/warning message box shown on the
  scanner page when an upload is rejected.

## Hover effects, transitions, and `:hover`

```css
.btn-dark:hover { background: var(--rose); color: var(--white); transform: translateY(-1px); box-shadow: 0 8px 24px rgba(196,131,106,0.35); }
```

`:hover` is a **pseudo-class** — a special kind of selector that only
applies while a specific condition is true, here "only while the mouse
cursor is currently positioned over this element." `transform: translateY(-1px)`
shifts the element up very slightly (1 pixel), and combined with the change
in `box-shadow`, this creates a subtle "lifting up" effect purely through
CSS, with no JavaScript involved at all. The smoothness of that change
(rather than it snapping instantly) comes from a `transition` property
defined on the base `.btn` rule, telling the browser to smoothly animate
certain properties over a short duration whenever they change, rather than
jumping to the new value immediately.

## The responsive breakpoint

```css
@media (max-width: 900px) {
  .site-nav { padding: 1rem 1.5rem; flex-wrap: wrap; }
  .nav-links { order: 3; width: 100%; justify-content: center; }
  .site-footer { padding: 1.5rem; }
  .footer-inner { flex-direction: column; text-align: center; }
}
```

As explained in `index_html.md`, a `@media` rule only applies under a
specific condition — here, only on screens 900 pixels wide or narrower
(phones and small tablets). This particular one adjusts the nav bar and
footer to work better on a small screen: reducing their padding, and
switching the footer's layout from a horizontal row to a stacked vertical
column (`flex-direction: column`) so its contents don't get uncomfortably
squeezed onto a narrow screen.

## What used to be here and was intentionally removed

An earlier version of this file included leftover CSS for a login/register
form (`.form-group`, `.form-label`, `.form-control`) and an "account" area
in the nav bar (`.nav-right`, `.nav-user`) — styling for a feature that was
never actually built into any real page in this project. Since nothing in
any current template referenced these classes at all, they were removed:
keeping unused styling around just makes a file longer and harder to trust
("is this actually being used somewhere I haven't found yet?"), for no
actual benefit.
