# templates/admin.html — explained for someone who has never written code

The admin dashboard — a page only an admin account can see, listing every
signed-up user with the option to delete one. Extends `base.html`, same
pattern as every other page (read `base_html.md` first).

## The table

```html
<table class="table table-striped mt-3">
  <thead>
    <tr>
      <th>ID</th>
      <th>Username</th>
      <th>Admin</th>
      <th>Joined</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    {% for user in users %}
    <tr>
      <td>{{ user.id }}</td>
      <td>{{ user.username }}</td>
      <td>{{ "Yes" if user.is_admin else "No" }}</td>
      <td>{{ user.created_at }}</td>
      <td>...</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```
An HTML `<table>` is built from `<thead>` (the header row) and `<tbody>`
(the actual data rows). `{% for user in users %}` loops once per user in
the `users` list that `main.py`'s `admin()` route passed in (built by
`auth.py`'s `get_all_users()`) — the same list-and-loop pattern already
used elsewhere in this project (see `about_html.md`'s conditions grid).
`{{ "Yes" if user.is_admin else "No" }}` is a compact **Jinja inline
if/else** — it evaluates the condition right there and produces one of two
short pieces of text, rather than needing a full multi-line `{% if %}` block
for something this simple.

## The delete button, per row

```html
<td>
  {% if user.id != session.user_id %}
  <form method="POST" action="/admin/delete/{{ user.id }}" class="delete-user-form">
    <button type="submit" class="btn btn-sm btn-danger">Delete</button>
  </form>
  {% endif %}
</td>
```
Each row that isn't the *currently logged-in admin's own row* gets a small
form with just a single Delete button. `action="/admin/delete/{{ user.id }}"`
builds the actual submission address by inserting that specific row's user
id directly into the URL — so deleting the user in row 7 submits to
`/admin/delete/7`, deleting the user in row 12 submits to `/admin/delete/12`,
and so on. `main.py`'s route `@app.route("/admin/delete/<int:user_id>", methods=["POST"])`
is written specifically to capture whatever number appears in that
position of the URL and hand it to the route function as `user_id` (see
`main.md`).

`{% if user.id != session.user_id %}` is a **UI courtesy**, not the real
protection — it just avoids showing an admin a delete button that would
target their own account, to prevent an accidental click. The actual rule
that stops self-deletion lives in `main.py`'s `admin_delete_user()` route
itself, which independently re-checks this on the server no matter what
the page happened to show — so even if this template check were somehow
bypassed, deleting your own account through this feature still wouldn't
be possible.

## The confirmation popup

```html
{% block extra_js %}
<script>
document.querySelectorAll(".delete-user-form").forEach(function (form) {
  form.addEventListener("submit", function (event) {
    if (!confirm("Delete this user? This cannot be undone.")) {
      event.preventDefault();
    }
  });
});
</script>
{% endblock %}
```
`document.querySelectorAll(".delete-user-form")` finds *every* delete form
on the page at once (there could be many, one per user row) — unlike
`getElementById`, which only ever finds one specific element, `querySelectorAll`
finds every match and returns them all together. `.forEach(function (form) { ... })`
then runs the same setup on each one individually.

`confirm("...")` is a built-in browser popup with an OK/Cancel choice —
it pauses everything and waits for the admin to respond. If they click
Cancel, `confirm(...)` returns `false`, so `!confirm(...)` is `true`, and
`event.preventDefault()` stops the form from actually submitting — nothing
happens, the user stays in the list. If they click OK, the form submits
normally, exactly as if this script didn't exist at all.

**This is a user-experience safeguard against an accidental mis-click,
not a security control.** Nothing stops someone from submitting a delete
request directly (e.g. with a tool other than a browser) and skipping this
popup entirely — which is exactly why the real safety rules (can't delete
yourself, can't delete the last remaining admin) are enforced in `main.py`
on the server, not here in JavaScript that only runs in a cooperating
browser.
