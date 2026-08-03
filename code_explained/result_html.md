# templates/result.html — explained for someone who has never written code

The results page — the biggest and most data-driven template in the whole
project, since it has to display everything about one prediction: the
Grad-CAM comparison image, all 8 confidence scores, and the full
recommendation. Like the other pages, it extends `base.html` — read
`base_html.md` first if you haven't already.

## Where its data comes from

Recall from `main.md` that `main.py`'s `/analyze` route renders this
template with three pieces of data attached: `prediction` (a dictionary
built by `model_inference.py`'s `predict()` function), `recommendation` (a
dictionary from `recommendation_engine.py`'s `get_recommendation()`), and
`preview_uri` (the uploaded photo, encoded as a data URI). Every `{{ ... }}`
value used throughout this file reads from one of those three.

## The Grad-CAM comparison slider

```html
{% if prediction.gradcam_uri %}
<div class="comp-viewport" id="comp-viewport">
  <img class="comp-img" src="{{ prediction.gradcam_uri }}" alt="AI focus map" draggable="false" />
  <img class="comp-img comp-original" id="comp-original" src="{{ preview_uri }}" alt="Your skin photo" draggable="false" />
  <span class="comp-label comp-label-left">Your Photo</span>
  <span class="comp-label comp-label-right">AI Focus Map</span>
  <span class="comp-hint" id="comp-hint">← drag to compare →</span>
  <div class="comp-handle" id="comp-handle"> ... </div>
</div>
{% else %}
<div class="photo-only">
  <img src="{{ preview_uri }}" alt="Uploaded skin photo" />
</div>
{% endif %}
```

`{% if prediction.gradcam_uri %} ... {% else %} ... {% endif %}` is a Jinja
**if/else** — it checks whether `prediction.gradcam_uri` has a real value
or not, and shows one of two completely different pieces of HTML depending
on the answer. `gradcam_uri` can end up empty (`None`) if Grad-CAM
generation happened to fail for some reason — `model_inference.py` is
deliberately written so that a Grad-CAM failure never crashes the whole
prediction, it just quietly results in no heatmap being available. In that
case, this page gracefully falls back to just showing the plain uploaded
photo (the `{% else %}` branch), instead of showing a broken image or an
error.

When Grad-CAM *did* work, two images are layered exactly on top of each
other in the same box: the AI's heatmap image underneath, and the original
uploaded photo on top of it. The original photo has a CSS `clip-path` rule
applied that hides the right half of it, so what's actually visible is the
original photo on the left side and the heatmap peeking through on the
right side, with a visible line between them where the clip cuts off. All
of this is `result.js`'s job to make draggable — that file changes exactly
where that clip-path cutoff is, in real time, as the visitor drags across
the image (see `result_js.md`).

`draggable="false"` on both `<img>` tags turns off the browser's own
built-in "drag this image out of the page" behavior, which would otherwise
interfere with the custom drag-to-compare behavior this page implements
itself.

## The confidence-level pill

```html
{% if prediction.confidence >= 75 %}
  <span class="pill pill--green">{{ prediction.confidence }}% confidence</span>
{% elif prediction.confidence >= 50 %}
  <span class="pill pill--amber">{{ prediction.confidence }}% confidence</span>
{% else %}
  <span class="pill pill--coral">{{ prediction.confidence }}% confidence</span>
{% endif %}
```

`{% elif %}` means "else if" — a way of checking a second condition only if
the first one turned out false. This is a three-way decision: 75% or higher
confidence gets a green pill (a color usually associated with "good/safe"),
50–74% gets amber/orange (moderate), and anything below 50% gets a coral/red
pill (low confidence) — giving the visitor an instant visual read on how
sure the AI actually is, on top of the exact number.

## All 8 condition scores

```html
{% for p in prediction.all_probs %}
<div class="score-card {% if p.raw_label == prediction.predicted_class %}score-card--top{% endif %}">
  <div class="score-card-row">
    <span class="score-label">{% if p.raw_label == prediction.predicted_class %}★ {% endif %}{{ p.label }}</span>
    <span class="score-pct">{{ p.confidence }}%</span>
  </div>
  <div class="score-track"><div class="score-fill" data-width="{{ p.confidence }}" style="width:0%"></div></div>
</div>
{% endfor %}
```

`prediction.all_probs` is a list — built inside `model_inference.py` — of
all 8 possible conditions, each with its own confidence score, already
sorted from highest to lowest before it ever reaches this template. This
loop generates one small "score card" per condition.

Notice the `{% if p.raw_label == prediction.predicted_class %}` check
appears *twice*, in two different spots: once to add the extra CSS class
`score-card--top` (which `app.css` styles with a highlighted background and
border), and again to add a small `★` symbol right before the condition's
name. Both are checking the exact same thing — "is this particular row the
one the AI actually picked as its final answer?" — just used in two
different places to mark that one row visually in two ways at once.

`data-width="{{ p.confidence }}"` stores each bar's real percentage as a
custom HTML attribute (any attribute starting with `data-` is a standard
way to attach extra information to an element that isn't meant to be shown
directly, but can be read later by CSS or JavaScript). Combined with
`style="width:0%"` starting every bar at zero, this sets things up for
`result.js` to animate each bar growing to its real width when the page
loads (see `result_js.md`) — the actual final value is already sitting
there in `data-width`, just waiting to be applied.

## The three recommendation columns

```html
<div class="card rec-card">
  <span class="rec-icon">✨</span>
  <h3>Key Ingredients</h3>
  <div class="pills">
    {% for ingredient in recommendation.ingredients %}
      <span class="pill pill--rose">{{ ingredient }}</span>
    {% endfor %}
  </div>
</div>
```
The simplest of the three columns: loop over `recommendation.ingredients`
(a plain list of text, already split apart by `recommendation_engine.py`)
and show one pill per item.

```html
<div class="product-list">
  {% set icons = ['🧴','💧','🌿','☀️'] %}
  {% for product in recommendation.suggested_products %}
    <div class="product-item">
      <span class="product-icon">{{ icons[loop.index0 % icons|length] }}</span>
      <div>
        <p class="product-brand">{{ product.brand }}</p>
        <p class="product-name">{{ product.name }}</p>
      </div>
    </div>
  {% endfor %}
</div>
```
The middle column is slightly more involved. `{% set icons = [...] %}`
creates a small, fixed local list of four decorative emoji, right here in
the template. Inside the loop, each `product` is already a dictionary with
separate `.brand` and `.name` values (thanks to `_parse_product` in
`recommendation_engine.py`), so those are shown directly.

The icon assignment is the one genuinely clever line here:
`icons[loop.index0 % icons|length]`. `loop.index0` is a special variable
Jinja automatically provides inside any `{% for %}` loop — it's the current
position in the loop, starting from 0 (so 0 for the first item, 1 for the
second, and so on). `icons|length` gives the number of items in the `icons`
list (4). The `%` symbol is the **modulo** (remainder) operator — it
divides one number by another and gives back whatever's left over. So
`loop.index0 % 4` produces the repeating sequence `0, 1, 2, 3, 0, 1, 2, 3, ...`
no matter how many products there actually are. `icons[...]` then uses that
number to pick out one specific emoji from the list. The practical effect:
each product gets a different icon than the one before it, cycling back to
the start once all four icons have been used, regardless of whether there
are 3 products or 12 — without needing an icon to be stored as part of the
product data itself.

```html
<ul class="advice-list">
  {% for tip in recommendation.skincare_advice %}
    <li>{{ tip }}</li>
  {% endfor %}
</ul>
```
The simplest column of the three: a plain bulleted list (`<ul>` = unordered
list, `<li>` = one list item) built from `recommendation.skincare_advice`.

## The JavaScript, and the Jinja-to-JavaScript handoff

```html
{% block extra_script %}
<script>
  window.RESULT_CONFIDENCE = {{ prediction.confidence }};
</script>
<script src="{{ url_for('static', filename='js/result.js') }}"></script>
{% endblock %}
```

`result.js` is loaded from a separate, static `.js` file — and static
files are sent to the browser exactly as they are on disk, without ever
being processed by Jinja. That means `result.js` itself has no way to
contain something like `{{ prediction.confidence }}` and have it actually
work — Jinja syntax left inside a `.js` file would just be sent to the
browser as literal, meaningless text.

The small inline `<script>` block just above it solves this: it runs
*before* `result.js` loads, and it's still part of this Jinja-processed
HTML page, so `{{ prediction.confidence }}` here *does* get correctly
replaced with the real number. `window.RESULT_CONFIDENCE = ...` stores that
number as a plain JavaScript global variable, attached to `window` (a
built-in object representing the whole browser page, accessible from
anywhere in any script running on that page). `result.js`, once loaded
right after, can then simply read `window.RESULT_CONFIDENCE` to get that
same value — see `result_js.md` for what it does with it.
