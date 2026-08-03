# How to Build Tvisha From Scratch — A Step-by-Step Guide

This is for someone starting this exact project with nothing — no code,
no dataset, no model. It lays out the **order** things need to be built in
and **why** that order matters (what depends on what). Every file
mentioned here has its own much deeper, line-by-line explanation already
written in `code_explained/` — this document is the map connecting them,
not a replacement for those.

It's organized as five **branches** — big phases of work. Each one only
makes sense once the branch before it exists, because later branches
literally import/depend on earlier ones. If you want to actually use git
branches while building this, a suggested branch name is given for each
phase.

```
main
 ├─ branch: dataset-and-model        (Branch 1)
 ├─ branch: backend-core             (Branch 2)
 ├─ branch: frontend                 (Branch 3)
 ├─ branch: authentication           (Branch 4)
 └─ branch: admin-roles              (Branch 5)
```

---

## Branch 1 — `dataset-and-model`

**Goal**: end up with one file, `best_skin_model_8class.pth`, containing a
trained AI model. Nothing else in this whole project can be built or
tested meaningfully without this existing first, since the backend's whole
job is to load and run this file.

1. **Collect the dataset.** One folder per skin condition (this project
   ended up with 8: Redness, dark spots, inflammatory acne, blackheads,
   whiteheads, pigmentation, pores, wrinkles), each containing photos of
   that condition. Folder names become the class names automatically later
   (see `code_explained/model_inference.md`'s explanation of why
   `CLASS_NAMES`'s exact order matters).
2. **Clean the dataset.** Check for exact duplicate photos (same image
   saved twice, or copied into two folders by mistake) using a file-hash
   comparison, and remove them — otherwise a photo could end up in both
   the training set and the test set, quietly inflating how good the model
   looks.
3. **Check for class imbalance and mislabeling.** If one class has far
   fewer photos than the others, the model will be worse at recognizing
   it. If two classes visually overlap (this project found `dark spots`
   and `pigmentation` did), decide on a clear rule for which class
   ambiguous photos belong to, and apply it consistently.
4. **Build the training notebook** (`dataset.ipynb`, meant to run in
   Google Colab, which provides a free GPU). In order, inside the
   notebook itself:
   - Load the dataset and show the per-class image counts (sanity check).
   - Preprocessing pipeline: resize every image to a fixed size, apply
     data augmentation (random flips/rotations/color changes) so the
     model sees more variety than the raw photos alone provide.
   - Split into train/validation/test sets.
   - Define the model: start from a pretrained EfficientNet-B0 (a
     general-purpose image recognition network already trained on
     millions of photos) and replace its final layer so it outputs 8
     scores instead of its original 1,000.
   - Hyperparameter search: try a few combinations of optimizer/learning
     rate/epoch count on short mini-runs, and keep whichever combination
     scores best on the validation set.
   - Full training run using the winning combination, with early stopping
     (stop once validation performance stops improving, to avoid
     overfitting).
   - Evaluate on the test set (data the model never saw during training)
     — this produces the real, trustworthy accuracy number.
   - Save the trained weights to `best_skin_model_8class.pth`.
5. **Download the trained model file** out of Colab/Google Drive and place
   it in the project's root folder, alongside where `main.py` will
   eventually look for it.

Nothing in Branch 2 can be properly tested until this file exists.

---

## Branch 2 — `backend-core`

**Goal**: a working Flask app that can take an uploaded photo and return a
real prediction — no login, no styling polish yet, just the core pipeline
working end to end.

1. **Project scaffolding first**: `pyproject.toml` (or `requirements.txt`)
   listing the dependencies this needs (`flask`, `torch`, `torchvision`,
   `timm`, `pillow`, `grad-cam`, `opencv-python`), and a `.gitignore`
   (at minimum: virtual environment folders, `__pycache__/`, `*.pyc`).
   Nothing else can be installed/run without this.
2. **`model_inference.py`** — build this before `main.py`, since `main.py`
   will need to import from it. Contains: the list of class names, a
   function to load the trained model file from Branch 1, a function to
   run one photo through the model and get a prediction, and a Grad-CAM
   function to generate the "what did the AI look at" heatmap. Full
   explanation: `code_explained/model_inference.md`.
3. **`face_validation.py`** — a photo-quality gate that runs *before* a
   photo reaches the model: checks it isn't too blurry/dark/bright, and
   if a face is detected, crops down to just the face; if no face is
   found, the photo is still accepted (treated as a close-up skin patch).
   Doesn't depend on `model_inference.py` at all — could be built in
   either order relative to step 2, but both need to exist before
   `main.py`. Full explanation: `code_explained/face_validation.md`.
4. **`recommendation_engine.py`** — reads `static/data/skin_recommendations.csv`
   and looks up ingredients/products/advice for a given predicted class.
   Independent of the other two files. Full explanation:
   `code_explained/recommendation_engine.md`.
5. **`main.py`** — only makes sense once steps 2-4 all exist, since it
   imports from all three. Defines the Flask app, loads the model once at
   startup, and the core routes: home page, about page, and `/analyze`
   (receives the uploaded photo, runs it through validation → prediction →
   recommendation lookup, in that order, and renders the results). Full
   explanation: `code_explained/main.md`.

At the end of this branch, you have a working app with no styling to speak
of and no accounts — but the actual AI pipeline is real and testable.

---

## Branch 3 — `frontend`

**Goal**: make the app actually presentable — real pages, real styling,
real interactivity — without changing anything about how the backend
works.

1. **`templates/base.html`** first — the shared page skeleton (fonts,
   stylesheet link, nav bar, footer script tag) that every other page
   extends. Building this before the individual pages avoids writing the
   same boilerplate four times. Full explanation: `code_explained/base_html.md`.
2. **`templates/index.html`, `templates/about.html`** — the two purely
   informational pages, each extending `base.html`. Full explanations:
   `code_explained/index_html.md`, `code_explained/about_html.md`.
3. **`templates/result.html`** — the results page `main.py`'s `/analyze`
   route renders. Needs to already know the exact shape of the data
   `model_inference.py`/`recommendation_engine.py` produce (from Branch 2)
   to display it correctly — `prediction.predicted_class`,
   `prediction.confidence`, `prediction.gradcam_uri`,
   `recommendation.ingredients`, and so on. Full explanation:
   `code_explained/result_html.md`.
4. **`static/css/`, `static/js/`** — the actual visual styling and
   interactive behavior (image preview, drag-and-drop, the Grad-CAM
   before/after slider). These reference specific HTML element `id`s from
   step 2/3's templates, so the templates need to exist first, or at
   least be written together with matching ids from the start.

At the end of this branch, the app looks and feels like a finished
product, but still has no concept of user accounts.

---

## Branch 4 — `authentication`

**Goal**: real signup/login/logout, and require being logged in to use the
scanner.

1. **`auth.py`** first — this is the one new file with no dependency on
   anything else in the project (just Python's built-in `sqlite3` and
   Werkzeug's password-hashing helpers, which come free with Flask).
   Contains: database setup (`init_db`), account creation
   (`create_user`), and login verification (`verify_user`). Full
   explanation: `code_explained/auth.md`.
2. **`main.py` additions** — import from `auth.py`, call `init_db()` once
   at startup (same pattern as loading the model in Branch 2), and add
   three new routes: `/signup`, `/login`, `/logout`, each reading/writing
   Flask's `session` (a secure, signed cookie that remembers who's logged
   in from page to page).
3. **`templates/login.html`, `templates/signup.html`** — simple forms
   extending `base.html`, submitting to the routes from step 2.
4. **Gate the scanner behind login** — two changes, both depending on
   `session` now existing from step 2:
   - In `main.py`'s `/analyze` route: reject the request server-side if
     nobody's logged in (the real, unbypassable check).
   - In `templates/index.html`: show the upload form only if logged in,
     otherwise show a "log in to continue" prompt (a UX nicety on top of
     the real server-side check, not a replacement for it).
5. **`templates/base.html` nav update** — show Login/Sign Up links when
   logged out, a Logout link when logged in, using the same `session`
   object.

This branch can only be built after Branch 3, since it modifies
`index.html` and `base.html` directly, and after Branch 2, since it
modifies `main.py`'s existing `/analyze` route.

---

## Branch 5 — `admin-roles`

**Goal**: one account tier (admin) that can see and manage every
registered user; everyone else is an ordinary user.

1. **`auth.py` additions** — add an `is_admin` column to the existing
   `users` table (with a safe migration check, since a real database from
   Branch 4 might already exist without this column), make `create_user`
   automatically grant admin to the very first account ever created (and
   nobody else, ever, through any other path), and add four new functions:
   `get_all_users`, `is_user_admin`, `count_admins`, `delete_user`.
2. **`main.py` additions** — store `is_admin` in the session alongside the
   existing login data (Branch 4's `signup`/`login` routes), and add two
   new routes: `/admin` (lists every user, admin-only) and
   `/admin/delete/<int:user_id>` (deletes one user, admin-only, with two
   safety rules: can't delete yourself, can't delete the last remaining
   admin).
3. **`templates/admin.html`** — a table of users with a delete button per
   row, extending `base.html` same as every other page.
4. **`templates/base.html` nav update** — show an "Admin" link, but only
   when `session.is_admin` is true (nested inside the existing
   logged-in check from Branch 4).

This branch depends entirely on Branch 4 already existing — there's no
concept of "admin" without accounts and sessions already working.

---

## Why this order, summarized

Each branch only becomes buildable once the one before it exists, because
of real, concrete dependencies — not just a suggested style:
- Branch 2 (`main.py`) directly imports from every file in Branch 2 itself
  and literally cannot load a model that doesn't exist yet (Branch 1).
- Branch 3's `result.html` needs to know the exact data shape Branch 2's
  `predict()` function produces, to display it.
- Branch 4 modifies files that already need to exist from Branch 3
  (`index.html`, `base.html`) and Branch 2 (`main.py`'s `/analyze`).
- Branch 5 modifies files that already need to exist from Branch 4
  (`auth.py`, `main.py`'s session handling, `base.html`'s nav).

Building out of this order is possible in places (e.g. styling could come
before the backend is fully working), but each branch's *first* step
always needs whatever it imports from to already exist, or it simply won't
run.
