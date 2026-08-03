# static/js/result.js — explained for someone who has never written code

This file runs on the results page. It does two separate jobs: animating
the confidence bars in when the page first loads, and making the Grad-CAM
before/after comparison draggable. See `scanner_js.md` first if you haven't
read it yet — the basics of what JavaScript is and how `.addEventListener`
works are explained there and won't be repeated in full here.

## Waiting for the page to fully load

```js
window.addEventListener('load', () => {
  ...
});
```

`window` represents the entire browser window/tab. The `'load'` event fires
once, after absolutely everything on the page — including images — has
finished loading. Everything in this file is wrapped inside this one
listener, because the code below needs to measure the exact pixel size and
position of an image on the page (for the drag-to-compare feature), which
can only be done reliably once that image has actually finished loading and
the browser has worked out its final size and position on the page.

## Reading the confidence value passed in from the HTML

```js
const target = window.RESULT_CONFIDENCE;
```

As explained in `result_html.md`, `result.html` sets
`window.RESULT_CONFIDENCE` to the real confidence percentage in a small
inline script, immediately before this file loads. This line simply reads
that value back out into a local variable called `target`, since this
static `.js` file can't contain the `{{ prediction.confidence }}` Jinja
syntax directly.

## Animating the confidence bars

```js
setTimeout(() => { document.getElementById('conf-bar').style.width = target + '%'; }, 200);

setTimeout(() => {
  document.querySelectorAll('.score-fill').forEach(el => { el.style.width = el.dataset.width + '%'; });
}, 400);
```

Both bars start out at `width: 0%` in the HTML/CSS (see `result_html.md`).
`setTimeout(functionToRun, delayInMilliseconds)` is a built-in JavaScript
tool that waits a certain number of milliseconds (1000 milliseconds = 1
second) before running the given function once. Here, after 200
milliseconds, the main confidence bar's actual width gets set to its real
value (`target + '%'`, e.g. `"87%"`). A separate `app.css` rule (a CSS
`transition`) is what makes that width change animate smoothly instead of
jumping instantly — this JavaScript code only decides *what* the final
width should be and *when* to apply it; the smooth animation itself is
CSS's job.

The second `setTimeout`, firing 200 milliseconds later (at the 400ms mark,
giving the two animations a slight, deliberate stagger instead of
happening at the exact same instant), handles all 8 of the smaller score
bars at once. `document.querySelectorAll('.score-fill')` finds *every*
element on the page with the class `score-fill` (note the plural — this is
different from `getElementById`, which only ever finds one specific
element by its unique id) and returns them all as a list-like collection.
`.forEach(el => { ... })` then runs the given function once for every
single one of those elements — `el` temporarily represents "whichever bar
we're currently looking at" each time through. `el.dataset.width` reads the
`data-width="..."` attribute that `result.html` set on each individual bar
(explained in `result_html.md`) — this is how each bar knows its own
correct final width, since they're all being processed together by the
same loop but each one needs a different final value.

## The Grad-CAM slider — setting up

```js
const viewport = document.getElementById('comp-viewport');
if (!viewport) return;
```

`comp-viewport` only exists in the page's HTML if Grad-CAM actually
succeeded (recall the `{% if prediction.gradcam_uri %}` check in
`result_html.md`). If it failed, this element simply won't be present on
the page, `getElementById` will return `null`, and `if (!viewport) return;`
— read as "if there is no viewport, stop running this function right
here" — prevents the rest of the drag-related code below from ever running
and trying to work with something that doesn't exist.

```js
const original = document.getElementById('comp-original');
const handle   = document.getElementById('comp-handle');
const hint     = document.getElementById('comp-hint');
let dragging = false, hintHidden = false;
```

Three more element references, same pattern as before. `let` (rather than
`const`) is used for `dragging` and `hintHidden` specifically because,
unlike the other variables in this file, their values are genuinely meant
to change over time as the visitor interacts with the slider — `dragging`
tracks whether the mouse button is currently held down, and `hintHidden`
tracks whether the "← drag to compare →" hint text has already been faded
out once.

## `setPos(clientX)` — the core of the slider

```js
function setPos(clientX) {
  const rect = viewport.getBoundingClientRect();
  let pct = (clientX - rect.left) / rect.width * 100;
  pct = Math.max(1, Math.min(99, pct));
  original.style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
  handle.style.left = pct + '%';
  if (!hintHidden && Math.abs(pct - 50) > 3) { hint.classList.add('hidden'); hintHidden = true; }
}
```

This function takes one input, `clientX` — the horizontal pixel position of
the mouse or finger on the *entire screen* — and does everything needed to
move the slider to match that position.

`viewport.getBoundingClientRect()` asks the browser exactly where this
element currently sits on screen and how big it is, returning an object
with values like `.left` (the pixel position of its left edge) and
`.width` (its width in pixels).

`(clientX - rect.left) / rect.width * 100` converts the raw screen position
into a percentage of the way across the slider specifically. Subtracting
`rect.left` converts from "position on the whole screen" to "position
relative to the left edge of this box." Dividing by `rect.width` turns that
into a fraction between 0 and 1 (0 = at the very left edge, 1 = at the very
right edge). Multiplying by 100 converts that fraction into a percentage.

`Math.max(1, Math.min(99, pct))` clamps that percentage so it can never go
below 1% or above 99% — without this, the visitor could drag the handle
fully to one edge, at which point one of the two images would become
completely hidden.

`original.style.clipPath = \`inset(0 ${100 - pct}% 0 0)\`` is the line that
actually creates the visual reveal effect. This uses a **template
literal** — a JavaScript string written with backticks (`` ` ``) instead of
regular quotes, which allows a value like `${100 - pct}` to be inserted
directly into the middle of the text. `clip-path: inset(top right bottom left)`
is a CSS property that hides parts of an element from each of its four
sides, by the given amounts. Here, only the *right* side amount changes,
based on the drag position: at `pct = 50` (the default, centered position),
the right 50% is hidden, showing exactly half of the original photo; as
`pct` increases (dragging right), less of the original photo's right side
gets hidden, revealing more of it; as `pct` decreases (dragging left), more
gets hidden.

`handle.style.left = pct + '%'` moves the visible drag-handle line to match
the same position, so it visually tracks wherever the reveal boundary
currently is.

The final `if` statement handles the small "← drag to compare →" hint text
that initially sits in the middle of the slider: `Math.abs(pct - 50)`
calculates how far the current position is from the exact center,
regardless of direction (`Math.abs` always returns a positive number,
turning e.g. `-15` into `15`). If that distance is more than `3`
(percentage points) — meaning the visitor has clearly started dragging away
from the center — and the hint hasn't already been hidden once before
(`!hintHidden`), the hint gets a `hidden` CSS class added to fade it out,
and `hintHidden` is set to `true` so this only ever happens once per page
visit, rather than the hint flickering in and out repeatedly as the
visitor drags back and forth near the center.

## Listening for mouse and touch input

```js
viewport.addEventListener('mousedown', e => { dragging = true; setPos(e.clientX); e.preventDefault(); });
document.addEventListener('mousemove', e => { if (dragging) setPos(e.clientX); });
document.addEventListener('mouseup', () => { dragging = false; });
viewport.addEventListener('touchstart', e => { dragging = true; setPos(e.touches[0].clientX); }, { passive: true });
document.addEventListener('touchmove', e => { if (dragging) setPos(e.touches[0].clientX); }, { passive: true });
document.addEventListener('touchend', () => { dragging = false; });
```

Two near-identical sets of three listeners each — one set for a mouse
(used on a desktop/laptop computer), one set for touch (used on a phone or
tablet), since browsers report these as genuinely different kinds of
events and both need to be handled for the slider to work everywhere.

- **`mousedown`/`touchstart`** — fires the instant the mouse button is
  pressed down (or a finger touches the screen) while over the slider.
  Sets `dragging` to `true`, and immediately calls `setPos` once right
  away so the slider jumps straight to wherever the visitor just
  pressed, rather than waiting for the first movement. `e.preventDefault()`
  (on the mouse version) stops the browser's own default text-selection/
  drag behavior from interfering. For touch, `e.touches[0]` is needed
  instead of `e.clientX` directly, because a touch event can technically
  report multiple simultaneous touch points (for multi-finger gestures);
  `[0]` just takes the first one.
- **`mousemove`/`touchmove`** — fires continuously as the mouse or finger
  moves, but the check `if (dragging)` means `setPos` is only actually
  called while a press is currently being held down — otherwise, simply
  moving the mouse anywhere on the page (not dragging anything) would move
  the slider, which isn't the intended behavior.
- **`mouseup`/`touchend`** — fires when the mouse button is released (or
  the finger lifts off the screen), setting `dragging` back to `false`, so
  further mouse/finger movement stops affecting the slider until the next
  press.

Two small details worth explaining: the move/release listeners are
attached to `document` (the whole page) rather than just `viewport` (the
slider box itself) — this is deliberate, so that if the visitor's cursor
happens to drift outside the slider's box while still holding the mouse
button down, dragging still continues to work correctly instead of
stopping the moment the cursor crosses the box's edge. And
`{ passive: true }` on the touch listeners is a small performance hint
telling the browser "this code will never try to block the page's normal
scrolling behavior," which lets the browser optimize touch-scrolling
performance on the rest of the page.
