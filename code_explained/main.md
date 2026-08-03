# main.py — explained for someone who has never written code

This is the most important file in the whole project. It's the file you
actually run to start the website. Think of it as the "control room" — it
doesn't do the AI thinking itself, and it doesn't do the face-checking
itself, but it's the piece that answers the phone when a visitor's browser
asks for a page, and it's the piece that calls all the other specialist
files to get their work done in the right order.

Before going through it line by line, a few basic ideas that the rest of
this document leans on:

- **A "function"** is a named, reusable block of instructions. You define it
  once with the word `def` (short for "define"), give it a name, and then
  you can "call" it (run it) as many times as you want just by writing its
  name followed by parentheses, e.g. `load_model(MODEL_PATH)`.
- **An "import"** is how one file borrows code that was written in another
  file (or in a library someone else published). Instead of retyping the
  same code everywhere, you write it once somewhere and `import` it wherever
  you need it.
- **A "variable"** is just a named box that holds a value — a number, some
  text, or something more complex. `MODEL_PATH = "best_skin_model_8class.pth"`
  creates a variable called `MODEL_PATH` and puts the text
  `"best_skin_model_8class.pth"` inside it.
- **An "if" statement** lets the program make a decision: "if this condition
  is true, do this; otherwise, skip it (or do something else)."
- **A "try/except" block** is Python's way of saying "attempt to do this
  risky thing, and if it fails with an error, don't crash the whole
  program — instead, run this backup code instead."

## The imports (lines 1–11)

```python
import argparse
import base64
import io
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from PIL import Image, UnidentifiedImageError

from auth import init_db, create_user, verify_user
from face_validation import validate_and_crop_face
from model_inference import load_model, predict, CLASS_NAMES, DISPLAY_NAMES, CONDITION_ICONS
from recommendation_engine import get_recommendation
```

Every one of these lines pulls in tools this file needs, but didn't write
itself:

- **`argparse`** — a tool built into Python for reading options typed after
  the program's name on the command line (like `--port 5001`).
- **`base64`** — a tool for turning raw file data (like a photo) into a long
  string of plain text characters. This matters later because a web page
  can display an image directly from a text string, without needing to save
  the image as a separate file first.
- **`io`** — short for "input/output." Gives us `io.BytesIO`, which lets us
  treat a chunk of data sitting in memory as if it were a file, without
  actually writing anything to the hard drive. This is faster and avoids
  leaving temporary files lying around.
- **`os`** — lets Python talk to the operating system, for example to read
  an environment variable (a setting stored outside the code itself).
- **`flask`** — this is the actual web framework: the toolkit that knows how
  to listen for a browser's request and send back a web page. We only
  import the specific pieces of Flask we actually use:
  - `Flask` — builds the web application itself.
  - `flash` — a way to store a short message ("Please select an image")
    that will be shown to the user on the *next* page they see.
  - `redirect` — sends the visitor's browser to a different page.
  - `render_template` — takes an HTML file and fills in any dynamic parts
    with real data, then returns the finished page.
  - `request` — gives access to whatever the visitor's browser just sent
    (like an uploaded file).
  - `url_for` — instead of typing a web address like `/scanner` by hand
    everywhere, this looks up the real address from the *name* of the
    function that handles it. If that address ever changed, every
    `url_for` call would still work correctly without editing anything.
  - `session` — a small, secure, per-visitor storage area (explained fully
    below, in the login section) used to remember that someone is logged
    in from one page to the next.
- **`PIL`** (Python Imaging Library, imported as `Image`/`UnidentifiedImageError`)
  — a library for opening, reading and manipulating image files.
- **The rest of the imports** pull in code from the *other* files in this
  project: `init_db`/`create_user`/`verify_user`/`get_all_users`/`delete_user`/
  `is_user_admin`/`count_admins` (from `auth.py`, see `auth.md`),
  `validate_and_crop_face` (from `face_validation.py`),
  `load_model`/`predict`/`CLASS_NAMES`/`DISPLAY_NAMES`/`CONDITION_ICONS`
  (from `model_inference.py`), and `get_recommendation` (from
  `recommendation_engine.py`). This is the literal, concrete meaning of
  "main.py ties everything together" — it's the one file that imports from
  every other file in the project.

## Creating the app (lines 13–14)

```python
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tvisha-dev-secret")
```

`Flask(__name__)` creates the actual website application and stores it in a
variable called `app`. `__name__` is a special built-in Python value that
just means "the name of this file" — Flask uses it internally to figure out
where to look for things like the `templates` folder.

`app.secret_key` is a bit of hidden, random-ish text that Flask uses to
digitally "sign" the flash messages mentioned above, so a visitor can't tamper
with them. `os.environ.get("SECRET_KEY", "tvisha-dev-secret")` means: "look
for a setting called `SECRET_KEY` in the computer's environment (a place
outside the code where secret values can be configured); if it's not set,
just use the plain text `"tvisha-dev-secret"` instead." This is a normal
pattern: sensitive settings can be supplied from outside the code when
running for real, but there's still a safe fallback for testing on your own
computer.

This same `secret_key` is also what makes logging in secure, explained next.

## Setting up the accounts database

```python
init_db()
```

This calls the function from `auth.py` (see `auth.md`) that creates the
`users` table if it doesn't already exist. Like loading the AI model below,
this is done once, right when the server starts — not on every visit.

## Settings kept together (lines 16–18)

```python
MODEL_PATH = "best_skin_model_8class.pth"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
```

Three variables, each holding a setting the app needs later:
- `MODEL_PATH` — the filename of the trained AI model on disk.
- `ALLOWED_EXTENSIONS` — a **set** (a collection where every value is
  unique and unordered) of file extensions that are allowed to be uploaded.
- `MAX_UPLOAD_SIZE_BYTES` — the biggest file size allowed, in bytes. A byte
  is the smallest unit computers measure data in; `10 * 1024 * 1024` is
  just Python doing the multiplication itself to work out how many bytes
  are in 10 megabytes, so the code reads clearly as "10 MB" instead of a
  meaningless big number like `10485760`.

Putting these at the top of the file, with clear names, means if you ever
need to change the size limit or allowed file types, there's exactly one
obvious place to look — instead of that number being buried inside a much
longer block of code further down.

## Loading the AI model once (lines 20–25)

```python
try:
    model = load_model(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")
except FileNotFoundError as e:
    model = None
    print(f"WARNING: {e}")
```

This code runs exactly once — the moment the web server starts up, before
it accepts any visitors at all. It calls the `load_model` function (which
lives in `model_inference.py`) and stores the result in a variable called
`model`. Loading a trained AI model from disk takes a moment and uses a fair
amount of memory, so this is deliberately done just once and kept around,
rather than reloading it fresh for every single visitor — that would make
every photo upload painfully slow.

The `try`/`except` here is a safety net. If `MODEL_PATH` doesn't actually
point to a real file (for example, someone forgot to put the trained model
file in the project folder), `load_model` would raise a `FileNotFoundError`
— Python's way of signalling "something went wrong." Instead of letting that
error crash the entire website before it even starts, the `except` block
catches it, sets `model` to `None` (Python's special "nothing here" value),
and prints a warning message to the terminal so a developer can see what
happened. The website still starts up either way — it just won't be able to
analyze photos until the model file problem is fixed.

## `f"..."` strings

`f"Model loaded from {MODEL_PATH}"` is called an **f-string**. The `f`
before the quotation mark tells Python "look inside the curly braces `{}`
for a variable, and substitute its actual value into the text." So if
`MODEL_PATH` holds `"best_skin_model_8class.pth"`, this line prints
`Model loaded from best_skin_model_8class.pth`.

## The four routes

A **route** in Flask is a rule that says "when a visitor's browser asks for
this specific web address, run this specific function." Each one is marked
with a line starting `@app.route(...)` directly above a function definition
— this is called a **decorator**, and it's Python's way of attaching extra
behavior to a function without having to change the function's own code.

### `/` — the home page

```python
@app.route("/")
def index():
    return render_template("index.html")
```
When someone visits the website's root address (just the domain name, with
nothing after it), this function runs. All it does is hand back the
`index.html` page, unchanged.

### `/about` — the about page

```python
@app.route("/about")
def about():
    conditions = [
        {"name": DISPLAY_NAMES[c], "icon": CONDITION_ICONS[c]}
        for c in CLASS_NAMES
    ]
    return render_template("about.html", conditions=conditions)
```
This one builds up some data before showing the page. `CLASS_NAMES` is a
list of the 8 skin condition names the AI can recognize (this list lives in
`model_inference.py`). The line inside the square brackets is called a
**list comprehension** — a compact way of building a new list by looping
over an existing one. In plain English, it means: "for every condition name
`c` in `CLASS_NAMES`, create a small dictionary containing its friendly
display name and its icon, and collect all of those into a new list called
`conditions`." A **dictionary** in Python is a collection of `key: value`
pairs — here, each one has a `"name"` key and an `"icon"` key. That
finished list is then handed to `about.html`, which loops over it to show
one card per condition (see `about_html.md` for that part).

### `/scanner` — the upload page

```python
@app.route("/scanner")
def scanner():
    return render_template("scanner.html")
```
Same idea as the home page — just shows the upload form, with nothing extra
computed first.

### `/signup`, `/login`, `/logout` — accounts

These three routes are what makes real accounts possible. First, a concept
they all depend on:

**What a session is.** HTTP (the protocol a browser and server talk over)
is fundamentally forgetful — every single request is its own isolated
conversation, with no built-in memory of any earlier request. So how does
the site remember you're logged in as you click from page to page? Flask's
`session` object solves this: the first time it's written to, Flask creates
a small piece of data, cryptographically **signs** it using `app.secret_key`
(set up earlier in this file), and sends it to the browser as a cookie. On
every later request, the browser automatically sends that same cookie back,
and Flask checks the signature and reads the data back out. "Signing" means
the data can be read and verified, but not *forged* — a visitor could look
at or even edit the cookie in their browser, but without knowing the secret
key (which only the server has), they can't produce a fake signature that
Flask would accept. This is why `app.secret_key` being set is what makes
`session` usable and trustworthy at all.

```python
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3:
            flash("Username must be at least 3 characters long.")
            return redirect(url_for("signup"))
        if len(password) < 6:
            flash("Password must be at least 6 characters long.")
            return redirect(url_for("signup"))
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("signup"))

        if not create_user(username, password):
            flash("That username is already taken. Please choose another.")
            return redirect(url_for("signup"))

        user = verify_user(username, password)
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = user["is_admin"]
        flash("Account created! You're now logged in.")
        return redirect(url_for("index"))

    return render_template("signup.html")
```
`methods=["GET", "POST"]` means this one route handles *two* different
situations with the same address: a plain **GET** (just visiting `/signup`
in a browser) shows the empty form (the last line, `return render_template("signup.html")`),
while a **POST** (submitting that form) runs everything above it instead.
`if request.method == "POST":` is what tells these two cases apart.

`request.form.get("username", "").strip()` reads the submitted form field
named `"username"` (defaulting to an empty string if somehow missing), and
`.strip()` removes any accidental leading/trailing spaces. The three `if`
checks re-validate everything the form's own HTML `required`/`minlength`
attributes already hinted at — deliberately, since browser-side checks are
easy to bypass, so the real rules live here on the server. `create_user`
(from `auth.py`) returns `False` if the username was already taken; if so,
a flash message explains why and the user is sent back to try again.

If everything succeeds, notice the code calls `verify_user` **again**
right after `create_user` succeeded — this looks slightly redundant, but
it's the simplest way to get back the newly created user's database `id`
(and admin status) without changing `create_user`'s own return value
(a plain `True`/`False`) into something more complicated. `session["user_id"] = ...`,
`session["username"] = ...`, and `session["is_admin"] = ...` then log the
new user in immediately — no separate "now go log in" step is needed. If
this happens to be the very first account ever created, `user["is_admin"]`
will be `True` (see `auth.md`'s explanation of `create_user`), and this
person is now an admin for the rest of this login session.

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verify_user(username, password)
        if user is None:
            flash("Invalid username or password.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash("Logged in successfully.")
        return redirect(url_for("index"))

    return render_template("login.html")
```
Same GET/POST pattern (with `session["is_admin"]` set here too). `verify_user`
(see `auth.md`) returns `None` if either the username doesn't exist *or*
the password is wrong — deliberately not distinguishing between those two
cases in the message shown ("Invalid username or password." either way),
so a stranger can't use this form to figure out which usernames are
actually registered.

```python
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("is_admin", None)
    flash("You have been logged out.")
    return redirect(url_for("index"))
```
`session.pop("user_id", None)` removes that key from the session if it's
there (the second argument, `None`, means "don't raise an error if the key
happens to already be missing"). Once all three keys are gone, the visitor
is logged out — any later check for `"user_id" in session` will now be
false, and the nav bar's admin link disappears along with it.

### `/admin` and `/admin/delete/<int:user_id>` — the admin dashboard

```python
@app.route("/admin")
def admin():
    if "user_id" not in session or not session.get("is_admin"):
        flash("You do not have permission to view that page.")
        return redirect(url_for("index"))

    users = get_all_users()
    return render_template("admin.html", users=users)
```
This is the **role-based access control** for the whole admin feature, in
plain terms: not every logged-in visitor is allowed to see this page —
only ones whose session says `is_admin` is true. `session.get("is_admin")`
reads that value safely (returning `None`/falsy if it isn't set at all,
rather than raising an error the way `session["is_admin"]` would for a
logged-out visitor with no such key). If either check fails — not logged
in at all, or logged in but not an admin — the visitor is redirected away
with an explanatory flash message, and `get_all_users()` (from `auth.py`)
is never even called. Only once both checks pass does the function fetch
the full user list and hand it to `admin.html` to display (see
`admin_html.md`).

```python
@app.route("/admin/delete/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    if "user_id" not in session or not session.get("is_admin"):
        flash("You do not have permission to do that.")
        return redirect(url_for("index"))

    if user_id == session["user_id"]:
        flash("You cannot delete your own account from this page.")
        return redirect(url_for("admin"))

    if is_user_admin(user_id) and count_admins() <= 1:
        flash("Cannot delete the last remaining admin account.")
        return redirect(url_for("admin"))

    delete_user(user_id)
    flash("User deleted.")
    return redirect(url_for("admin"))
```
`<int:user_id>` in the route's address is a **URL converter** — it tells
Flask "expect a whole number in this part of the address, convert it from
text automatically, and pass it into the function as `user_id`." So a
request to `/admin/delete/7` runs this function with `user_id` already
equal to the integer `7`, ready to use directly, no manual conversion
needed.

Notice the exact same `"user_id" not in session or not session.get("is_admin")`
check appears again here, identical to the one in `admin()` just above.
This is **deliberate duplication, not an oversight**: someone could send a
request straight to this exact address (e.g. with `curl -X POST`) without
ever having loaded `/admin` in a browser first, so each route that needs
protecting must check for itself — one route's check does nothing to
protect a completely different route.

Two more checks run before anything is actually deleted:
- `if user_id == session["user_id"]:` — stops an admin from deleting their
  own account through this page, which would otherwise be an easy way to
  accidentally lock yourself out.
- `if is_user_admin(user_id) and count_admins() <= 1:` — stops the *last*
  remaining admin account from being deleted at all (by anyone, including
  another admin). This matters because, per `auth.md`'s explanation of
  `create_user`, the only way to ever become an admin is being the very
  first person to sign up — if every admin account were ever deleted,
  there would be no way for *anyone* to regain admin access afterward
  through the app itself.

Only if both checks pass does `delete_user(user_id)` (from `auth.py`)
actually run.

### `/analyze` — where a photo actually gets processed

```python
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_id" not in session:
        flash("Please log in to analyze your skin.")
        return redirect(url_for("login"))
```
This route is different: `methods=["POST"]` means this address only
responds to a **POST** request — the kind of request a browser sends when
submitting a form (as opposed to a **GET** request, which is what happens
when you just click a link or type an address). This is the function that
does all of the real work, step by step:

**Step 0 — is anyone actually logged in?**
This check runs before anything else in the function. `"user_id" not in session`
is `True` for a visitor who never logged in (their `session` dictionary is
empty) — they get sent to `/login` instead of having their photo
processed. Crucially, this is a **server-side** check: even someone who
skips the website's own upload page entirely and sends a photo straight
to `/analyze` with a tool like `curl` (bypassing the HTML/JavaScript
completely) would still hit this exact check and get rejected, since there
would be no valid, signed session cookie in that request either. Hiding
the upload form in the page for logged-out visitors (see `index_html.md`)
is a nice user experience, but this line here is the part that actually
enforces the rule.

**Step 1 — is the AI model even available?**
```python
if model is None:
    flash("Model not loaded. Place best_skin_model_8class.pth in the project root.")
    return redirect(url_for("scanner"))
```
Remember `model` might be `None` if loading it failed earlier. If so, there's
no point continuing — show an error message and send the visitor back to
the scanner page. `redirect(url_for("scanner"))` means "send their browser
to whatever address the `scanner` function is responsible for" (which is
`/scanner`) — using the function's name rather than typing `"/scanner"`
directly, for the same reason explained under `url_for` above.

**Step 2 — was a file actually submitted?**
```python
file = request.files.get("skin_image")
if not file or file.filename == "":
    flash("Please select an image before submitting.")
    return redirect(url_for("scanner"))
```
`request.files` holds any files the browser sent along with the form.
`.get("skin_image")` looks specifically for a file that was sent under the
name `"skin_image"` — this name has to exactly match the `name="skin_image"`
attribute on the file input in `scanner.html`, or nothing would be found here.
If no file came through at all, or an empty filename was somehow submitted,
reject it with a message.

**Step 3 — is the file type allowed?**
```python
ext = file.filename.rsplit(".", 1)[-1].lower()
if ext not in ALLOWED_EXTENSIONS:
    flash("Unsupported file type. Please upload PNG, JPG, JPEG, or WEBP.")
    return redirect(url_for("scanner"))
```
`file.filename` is the original name of the uploaded file, e.g.
`"myphoto.JPG"`. `.rsplit(".", 1)` splits that name into pieces wherever
there's a `.`, but only splits once, starting from the right-hand side —
so `"myphoto.JPG"` becomes `["myphoto", "JPG"]`. `[-1]` grabs the last item
in that list (the extension), and `.lower()` converts it to lowercase, so
`"JPG"` and `"jpg"` are treated the same. That result is then checked
against `ALLOWED_EXTENSIONS` (defined near the top of the file).

**Step 4 — is the file too big?**
```python
image_bytes = file.read()
if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
    flash("File too large. Maximum size is 10 MB.")
    return redirect(url_for("scanner"))
```
`file.read()` actually reads the file's raw contents into memory as a
sequence of bytes. `len(...)` gives the number of bytes, which is compared
against the size limit set earlier.

**Step 5 — is it really a valid image?**
```python
try:
    uploaded_image = Image.open(io.BytesIO(image_bytes))
    uploaded_image.load()
except UnidentifiedImageError:
    flash("Could not read that image. Please try a different file.")
    return redirect(url_for("scanner"))
```
`io.BytesIO(image_bytes)` wraps the raw bytes so they can be handled as if
they were a file on disk, without actually saving anything. `Image.open(...)`
asks the PIL library to interpret that data as an image, and `.load()`
forces it to actually read through the whole thing right away (catching
corrupted files that might otherwise only fail later, at an inconvenient
moment). If the data isn't a real, readable image at all — say, someone
renamed a text file to `photo.jpg` — PIL raises `UnidentifiedImageError`,
which is caught here and turned into a friendly message instead of a crash.

**Step 6 — check the photo shows a usable face/skin patch**
```python
face_image, face_error = validate_and_crop_face(uploaded_image)
if face_error:
    flash(face_error)
    return redirect(url_for("scanner"))
```
This calls the function from `face_validation.py` (see `face_validation.md`
for everything it checks). It always returns **two values at once** — this
is a Python feature called **tuple unpacking**: the function returns a pair
of values, and `face_image, face_error = ...` assigns the first one to
`face_image` and the second to `face_error` in one line. If the photo was
rejected for any reason (too blurry, too dark, multiple faces, etc.),
`face_error` will contain a message explaining why, and that gets shown to
the user. If the photo was fine, `face_error` is `None` and `face_image`
holds the (possibly cropped) image, ready for the next step.

**Step 7 — turn the processed photo into raw bytes again**
```python
face_buf = io.BytesIO()
face_image.save(face_buf, format="PNG")
face_bytes = face_buf.getvalue()
```
`face_image` at this point is a PIL image object (a representation of the
picture inside Python's memory), not raw bytes. Before it can be handed to
the AI model or displayed on a web page, it needs to be turned back into
an actual sequence of bytes, in a standard image format (PNG here).
`io.BytesIO()` (with nothing inside the parentheses this time) creates an
empty "virtual file" in memory, `.save(...)` writes the image into it, and
`.getvalue()` reads back everything that was written, as raw bytes stored
in the `face_bytes` variable.

**Step 8 — run the actual AI prediction and look up advice**
```python
result = predict(model, face_bytes)
recommendation = get_recommendation(result["predicted_class"])
```
`predict` (from `model_inference.py`) is where the trained neural network
actually looks at the photo and decides which of the 8 skin conditions it
most resembles. It returns a dictionary (`result`) containing the predicted
class name, a confidence percentage, and more (see `model_inference.md`
once that's written). `result["predicted_class"]` reads the specific value
stored under the `"predicted_class"` key of that dictionary, and hands it
to `get_recommendation` (from `recommendation_engine.py`), which looks up
matching skincare advice.

**Step 9 — prepare the photo for display without saving it as a file**
```python
preview_uri = "data:image/png;base64," + base64.b64encode(face_bytes).decode()
```
This turns the raw image bytes into a **data URI** — a special kind of web
address that contains the actual image data directly inside the text of the
address itself, instead of pointing to a separate file somewhere. `
base64.b64encode(face_bytes)` converts the raw bytes into base64 (a way of
representing binary data using only ordinary text characters, since raw
bytes can't be safely embedded directly inside HTML/text). `.decode()`
converts that result from Python's raw bytes format into an ordinary text
string. The `"data:image/png;base64,"` prefix at the start tells a web
browser exactly how to interpret what follows: "this is PNG image data,
encoded in base64." The final combined string can be dropped straight into
an `<img src="...">` tag in `result.html` and the browser will display it,
with no separate image file needed anywhere on disk.

**Step 10 — show the results page**
```python
return render_template(
    "result.html",
    prediction=result,
    recommendation=recommendation,
    preview_uri=preview_uri,
)
```
Finally, `render_template` builds the actual HTML page from `result.html`,
handing it three pieces of data it needs: the prediction results, the
recommendation, and the photo preview. Inside `result.html`, these become
available under the names `prediction`, `recommendation`, and `preview_uri`
— see `result_html.md` for how that template uses them.

## The bottom block — starting the server

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
```

`if __name__ == "__main__":` is a very common pattern in Python files that
can either be run directly or imported by another file. `__name__`
automatically equals the text `"__main__"` only when this particular file
is the one actually being executed (e.g. by typing `python main.py` in a
terminal) — if this file were instead imported from somewhere else, this
block would simply be skipped. This lets `main.py` be safely reused as a
building block elsewhere without accidentally starting a whole web server
as a side effect.

Inside that block: `argparse.ArgumentParser()` creates a helper for reading
command-line options. `.add_argument("--port", type=int, default=5001)`
tells it to look for an optional `--port` value, convert whatever's typed
after it into a whole number, and use `5001` if nothing was given.
`parser.parse_args()` actually reads whatever was typed on the command line
and stores the results in `args` — so `args.port` holds either the number
you typed after `--port`, or `5001` by default.

Finally, `app.run(debug=True, port=args.port)` actually starts the web
server, listening for visitors on the chosen port. A "port" is just a
numbered doorway on your computer that programs use to send/receive network
traffic. `debug=True` turns on Flask's developer mode, which shows
detailed, helpful error pages if something goes wrong while coding, instead
of a plain generic error.
