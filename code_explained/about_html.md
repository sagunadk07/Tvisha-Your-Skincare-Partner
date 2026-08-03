# templates/about.html — explained for someone who has never written code

The About page — explains how the app works and lists all 8 conditions the
AI can detect. Like `index.html`, it starts with
`{% extends "base.html" %}` and defines `title`, `extra_style`, and
`content` blocks (see `base_html.md` and `index_html.md` first for the
basics of how that all works, since this file follows the exact same
pattern and won't repeat those explanations).

## The layout, section by section

```html
{% block content %}
<div class="about-hero"> ... </div>
<div class="mission-strip"> ... </div>
<div class="section"> ... How It Works ... </div>
<div class="section"> ... 8 Conditions Detected ... </div>
{% endblock %}
```

Four stacked sections, top to bottom:

1. **`about-hero`** — a short intro paragraph at the very top.
2. **`mission-strip`** — a full-width, dark-colored band with a short
   mission statement. Visually, this breaks up the page and creates a clear
   separation between the intro and the more detailed sections below it.
3. **First `.section`** — "How It Works," explained next.
4. **Second `.section`** — "8 Conditions Detected," explained after that.

## "How It Works" — a genuinely numbered sequence

```html
<div class="steps">
  <div class="card card--hover step">
    <span class="step-num">01</span>
    <h3>Upload a Photo</h3>
    <p>...</p>
  </div>
  <div class="card card--hover step">
    <span class="step-num">02</span>
    <h3>AI Classifies It</h3>
    ...
  </div>
  ...
</div>
```

Four cards, each with a number, a short heading, and a sentence of
explanation, describing Upload → AI Classifies → See What the AI Saw → Get
Recommendations. These are written out individually rather than generated
by a loop, because there are only four of them, they're fixed and won't
change, and each one has entirely different text — a loop would actually
add complexity here rather than reduce it. The numbers `01`–`04` are
included deliberately because this genuinely *is* a sequence — each step
really does happen after the one before it in the real pipeline — so
numbering the steps conveys real, true information about the process,
rather than being decoration for its own sake.

## "8 Conditions Detected" — a data-driven loop

```html
<div class="cond-grid">
  {% for c in conditions %}
  <div class="card card--hover cond-card">
    <span class="cond-icon">{{ c.icon }}</span>
    <span class="cond-name">{{ c.name }}</span>
  </div>
  {% endfor %}
</div>
```

This is different from the fixed four steps above — here, one very similar
little card needs to be repeated eight times, once per condition, and the
content of each one comes from real data rather than being hand-written.

`{% for c in conditions %} ... {% endfor %}` is a Jinja **for loop** — it
repeats everything between those two tags once for every single item found
in `conditions`. `conditions` itself is a Python list of small dictionaries,
built inside `main.py`'s `about()` function (see `main.md`) and passed into
this template when the page is rendered. Each time around the loop, `c`
temporarily holds one of those dictionaries — the first time through, `c`
might be `{"name": "Skin Redness", "icon": "🔴"}`; the next time through a
different one, and so on, until all 8 have been used.

`{{ c.icon }}` and `{{ c.name }}` read the specific values out of whichever
dictionary `c` currently holds, and insert them as plain text into the
page. So this small block of HTML, written once, actually produces eight
separate, slightly different-looking cards once the page is fully built —
one real card per skin condition. If the AI model were ever extended to
recognize a 9th condition, and that condition were added to `CLASS_NAMES`
in `model_inference.py`, this grid would automatically grow to show 9 cards
too, without a single line of this file needing to change — that's the
whole benefit of generating repeated content from a loop and real data,
instead of typing out each card by hand.

## No `extra_script` block

Same as the home page — the About page is entirely static text and data, no
JavaScript-driven interactivity, so it doesn't define this block at all.
