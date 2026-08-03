# templates/signup.html — explained for someone who has never written code

The account-creation form. Nearly identical to `login.html` (read that
file's doc first — this one only covers what's different) with one extra
field.

```html
<form method="POST" action="/signup">
  <div class="mb-3">
    <label for="username" class="form-label">Username</label>
    <input type="text" class="form-control" id="username" name="username" required minlength="3">
  </div>
  <div class="mb-3">
    <label for="password" class="form-label">Password</label>
    <input type="password" class="form-control" id="password" name="password" required minlength="6">
  </div>
  <div class="mb-3">
    <label for="confirm_password" class="form-label">Confirm Password</label>
    <input type="password" class="form-control" id="confirm_password" name="confirm_password" required minlength="6">
  </div>
  <button type="submit" class="btn btn-primary w-100">Create Account</button>
</form>
```

## What's different from the login form

- A third field, `confirm_password` — its value is compared against
  `password` in `main.py`'s `signup()` route, to catch a simple typo before
  creating the account.
- `minlength="3"` on username and `minlength="6"` on both password fields
  — like `required`, these are browser-side conveniences only (they give
  instant feedback without needing to submit the form first). They are
  **not** the real security boundary — someone could submit this form
  through a tool other than a browser and skip these checks entirely.
  The actual, trustworthy validation happens server-side, in `main.py`'s
  `signup()` route, which independently re-checks the same length rules
  and the passwords-match rule before ever calling `auth.py`'s
  `create_user()`. Never trust a check that only happens in the browser.

## What happens after submitting

`main.py`'s `signup()` route validates the input, then calls `auth.py`'s
`create_user()`. If the username's already taken, the database itself
rejects the insert (see `auth.md`'s explanation of the `UNIQUE` constraint
and `sqlite3.IntegrityError`), and a flash message says so. Otherwise, the
new account is created and the user is logged in immediately (no separate
"now go log in" step) — see `main.md` for the exact route code.
