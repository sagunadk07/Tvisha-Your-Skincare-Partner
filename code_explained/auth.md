# auth.py — explained for someone who has never written code

This file's job: store user accounts safely, and check a username/password
pair when someone tries to log in. It's the one file in this project that
talks to a **database** — everything else so far has read/written plain
files (a CSV, an image) or run a neural network.

## What a database actually is

A Python variable disappears the instant the program stops running — if
you stored a username in a normal variable, it would be gone the moment the
server restarted. A **database** is a special kind of file, built and
managed by dedicated software (here, **SQLite**), specifically designed to
store structured data permanently on disk and let you reliably add, look
up, and update it. Think of it like a very disciplined spreadsheet: it has
**tables** (like separate sheets — this file has one, called `users`),
each table has **columns** (fixed categories of information — here:
`id`, `username`, `password_hash`, `created_at`), and each **row** is one
individual record (one signed-up user).

**SQLite** specifically stores this entire database as a single ordinary
file on disk (`users.db`, created automatically the first time the app
runs) — no separate database server program needs to be installed or kept
running, which is why it's a good fit for a small project like this.
Python can talk to SQLite databases out of the box, via the `sqlite3`
module that ships with Python itself — no extra installation needed at all.

## The imports

```python
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
```
`sqlite3` is Python's built-in toolkit for talking to a SQLite database.
`werkzeug` is a library Flask itself is built on top of (it's automatically
installed the moment you install Flask) — `generate_password_hash` and
`check_password_hash` are two ready-made functions it provides specifically
for handling passwords safely, explained in detail below.

## `DB_PATH` and `get_connection()`

```python
DB_PATH = "users.db"

def get_connection():
    return sqlite3.connect(DB_PATH)
```
`DB_PATH` is just the filename the database will live in, right next to
`main.py`. `sqlite3.connect(DB_PATH)` opens a **connection** — a live link
between this running Python program and that database file, through which
commands can be sent. `get_connection()` is a small helper that other
functions in this file call every time they need to talk to the database,
so the actual filename only has to be written once.

## `init_db()` — setting up the table

```python
def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "is_admin" not in existing_columns:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()
```
`conn.execute("...")` sends a command written in **SQL** — Structured Query
Language, the standard language almost every database understands — to the
database. `CREATE TABLE IF NOT EXISTS users (...)` means: "make a table
called `users` with these columns, but only if one doesn't already exist" —
this makes the function **safe to run every single time the app starts**
(called from `main.py`, right after the app is created), since it won't
try to recreate (and error on) a table that's already there from a
previous run.

Each column definition explained:
- `id INTEGER PRIMARY KEY AUTOINCREMENT` — a unique whole number identifying
  each user, automatically assigned and increased by SQLite itself (1, 2,
  3, ...) — you never set this yourself.
- `username TEXT UNIQUE NOT NULL` — the username, stored as text. `UNIQUE`
  is a rule enforced by the database itself: it will refuse to let two
  different rows have the same username, ever. `NOT NULL` means this
  column can never be left empty.
- `password_hash TEXT NOT NULL` — explained fully below; never the actual
  password itself.
- `is_admin INTEGER NOT NULL DEFAULT 0` — `0` means an ordinary user, `1`
  means an admin. SQLite doesn't have a dedicated true/false type, so a
  whole number standing in for yes/no is the normal way to store this.
  `DEFAULT 0` means any row that doesn't explicitly specify a value gets
  `0` automatically.
- `created_at TEXT DEFAULT CURRENT_TIMESTAMP` — automatically records the
  date/time a row was created, without any code here needing to set it
  explicitly.

**What a schema migration is, and why the extra check exists.** A
database's "schema" is just the shape of its tables — which columns exist,
and what type each one is. When `is_admin` was added to this project after
the `users` table had already been created and used once before (with a
real signed-up account already sitting in it), `CREATE TABLE IF NOT EXISTS`
alone wouldn't help — it only creates a table if none exists yet; it does
nothing to an *existing* table that's simply missing a column. This is
exactly the kind of situation a **schema migration** handles: a small,
deliberate step that updates an already-existing database to match a
newer, changed structure. `PRAGMA table_info(users)` is a special SQLite
command ("PRAGMA") that describes the table's actual current columns;
`existing_columns` collects just their names. If `"is_admin"` isn't among
them, `ALTER TABLE users ADD COLUMN ...` adds it — every existing row
retroactively gets `0` (thanks to the same `DEFAULT 0`), and every future
row gets it automatically too. Checking first, rather than just always
running `ALTER TABLE`, avoids an error on every later app restart (SQLite
would otherwise complain that the column already exists).

`conn.commit()` saves the changes permanently to disk — without this, SQLite
can hold changes only temporarily. `conn.close()` closes the connection
since this function's job is done; leaving connections open unnecessarily
is generally avoided.

## What "hashing" a password means, and why

**Hashing is not the same thing as encryption.** Encryption is reversible —
if you have the right key, you can turn encrypted data back into the
original. Hashing is **one-way**: `generate_password_hash("mypassword123")`
turns that password into a long scrambled string, and there is no
function, no key, no operation that turns that scrambled string back into
`"mypassword123"`. It's mathematically designed to only go one direction.

Why store a hash instead of the real password? If the `users.db` file were
ever stolen, leaked, or (since this particular project's GitHub repo is
public) accidentally committed to git, an attacker with only the hashes
still couldn't read anyone's actual password. All the app itself needs to
do is check "does the password just typed in produce the *same* hash as
the one stored?" — it never needs to know or store the real password to do
that check.

`check_password_hash(password_hash, password)` does exactly that comparison
— given the stored hash and a freshly typed-in password, it re-runs the
same one-way hashing process on the typed-in password and checks if the
result matches. It returns `True` or `False`.

## `create_user(username, password)` — signing someone up

```python
def create_user(username, password):
    conn = get_connection()
    try:
        existing_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        is_admin = 1 if existing_count == 0 else 0
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), is_admin),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
```

**How the very first account becomes admin.** `SELECT COUNT(*) FROM users`
asks the database "how many rows currently exist in this table?" before
anything new is added. If that count is `0`, this new signup is about to
become the first row the table has ever had, so `is_admin` is set to `1`;
for every signup after that, the count is already `1` or more, so
`is_admin` stays `0`. This decision is made **once, right here, at the
exact moment of signing up** — there is no button, checkbox, or setting
anywhere that lets a visitor request admin status; the only way to become
admin is to be the very first person who ever creates an account on this
particular database. (Worth knowing as an honest, small limitation: this
count-then-insert isn't wrapped in an extra database lock, so if two people
somehow signed up in the exact same instant during the very first launch,
both could theoretically see a count of `0` — an acceptable edge case for a
small student project with no real concurrent traffic.)

`INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)` is
SQL for "add a new row to the `users` table with these three values." The
three `?`
marks are **placeholders** — instead of directly gluing the actual username
and password text into the SQL command as a string, the real values are
handed separately to `.execute(...)` as a tuple,
`(username, generate_password_hash(password), is_admin)`, and SQLite
safely inserts them in place of the `?` marks itself.

**This is critically important for security**, and worth a concrete
example of what could go wrong without it. Imagine instead writing:
```python
conn.execute(f"INSERT INTO users (username, password_hash) VALUES ('{username}', '...')")
```
If someone typed a username like `Bob', 'fake_hash'); DROP TABLE users; --`,
that text would get glued directly into the SQL command as if the attacker
had *typed the SQL themselves* — potentially deleting the entire table.
This kind of attack is called **SQL injection**. Using `?` placeholders
instead means the database always treats the given values as *plain data*,
never as commands to execute, no matter what characters they contain — so
this specific attack simply isn't possible here.

`generate_password_hash(password)` is called right here, at the moment of
signing up — so the real password only exists in memory for a brief
moment, and only the resulting hash ever gets written to the database.

The `try`/`except sqlite3.IntegrityError`/`finally` structure: recall the
`username` column has a `UNIQUE` rule enforced by the database itself. If
someone tries to sign up with a username that's already taken, the
`INSERT` command itself fails, and SQLite raises `sqlite3.IntegrityError`
— Python's way of saying "that broke a rule you set up." Rather than
manually checking "does this username already exist?" *before* trying to
insert (which has a subtle timing flaw if two people signed up with the
same name at almost the same instant), this code just attempts the insert
and catches the specific error if it fails — simpler and safer. If that
happens, the function returns `False` so `main.py` can show "username
taken." `finally: conn.close()` guarantees the connection gets closed
whether the insert succeeded or failed.

## `verify_user(username, password)` — logging someone in

```python
def verify_user(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, password_hash, is_admin FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    user_id, db_username, password_hash, is_admin = row
    if check_password_hash(password_hash, password):
        return {"id": user_id, "username": db_username, "is_admin": bool(is_admin)}
    return None
```
`SELECT id, username, password_hash, is_admin FROM users WHERE username = ?`
asks the database: "find the row in `users` whose `username` column
matches this value, and give me back its `id`, `username`, `password_hash`,
and `is_admin`." Again, `?` is a safe placeholder for the actual username,
exactly as explained above. `.fetchone()` retrieves a single matching row
(or `None` if no user with that username exists at all).

If `row` is `None`, the function immediately returns `None` — no such user.
Otherwise, the row's four values are unpacked into `user_id`,
`db_username`, `password_hash`, `is_admin`, and `check_password_hash`
compares the freshly-typed `password` against the stored hash. If it
matches, the function returns a small dictionary with the user's `id`,
`username`, and admin status — enough information for `main.py` to log
them in and remember whether they're an admin. `bool(is_admin)` converts
SQLite's stored `0`/`1` into a clean Python `True`/`False`. If it doesn't
match (wrong password), it returns `None`, same as "no such user" —
deliberately not distinguishing between "wrong password" and "username
doesn't exist" in what gets returned, so `main.py` can show one single
generic error message either way, without hinting to a stranger which
usernames are actually registered.

## The admin-management functions

```python
def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, is_admin, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "username": r[1], "is_admin": bool(r[2]), "created_at": r[3]}
        for r in rows
    ]
```
Used by the admin dashboard (`main.py`'s `admin()` route, `admin.html`).
`.fetchall()` (rather than `.fetchone()`, used everywhere else in this
file) retrieves *every* matching row, not just one — here that means every
single registered user. `ORDER BY id` sorts them by signup order (row 1
first). The list comprehension at the end converts each raw database row
(a plain tuple of four values in a fixed order) into a proper dictionary
with named keys, the same pattern used throughout this project for turning
row-based data into something a template can read by name
(`user.username`, `user.is_admin`, etc.) instead of by position.

```python
def is_user_admin(user_id):
    conn = get_connection()
    row = conn.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False
```
Looks up a single user by their numeric `id` (rather than `username`, used
elsewhere) and reports whether they're an admin. `bool(row[0]) if row else False`
is a compact inline if/else: if a matching row was found, convert its
`is_admin` value to `True`/`False`; if no such user exists at all
(`row` is `None`), just report `False` rather than crashing trying to read
`row[0]` from nothing.

```python
def count_admins():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1").fetchone()[0]
    conn.close()
    return count
```
Counts how many rows currently have `is_admin = 1`. Used by `main.py` to
enforce "never delete the last remaining admin" — since admin status can
only ever be granted by being the very first-ever signup (see
`create_user` above), losing every admin account would mean nobody could
ever access `/admin` again, with no way to grant it back through the app.

```python
def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
```
`DELETE FROM users WHERE id = ?` removes the one row matching that id. If
`user_id` doesn't actually match any row (already deleted, or never
existed), this simply matches and deletes zero rows — no error, nothing
happens. This function itself doesn't check *who's allowed* to call it or
*which* user is being deleted — those decisions (is the caller an admin?
are they trying to delete themselves? would this remove the last admin?)
are deliberately made in `main.py`'s route before this function is ever
called, keeping this function itself simple and single-purpose.
