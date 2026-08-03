# recommendation_engine.py — explained for someone who has never written code

This file's job: once the AI has decided which skin condition a photo shows,
this file looks up what advice to give the visitor — what ingredients help,
what products to consider, and what general skincare tips apply. It reads
all of that from a spreadsheet-like file instead of a database, which is a
perfectly reasonable, simple approach for a project this size.

## Background ideas

- **CSV** stands for "comma-separated values" — a very simple text file
  format for storing tables of data, similar to a basic Excel spreadsheet
  but saved as plain text. Each line is one row, and (usually) commas
  separate the columns. It can be opened and edited in Excel, Google
  Sheets, or even a plain text editor.
- **A dictionary** in Python is a collection of `key: value` pairs — like a
  real-world dictionary where you look up a word (the key) to find its
  definition (the value). Here, dictionaries are used to represent both one
  row of the CSV file, and the final recommendation handed back to the rest
  of the app.
- **A list** is an ordered collection of values, written with square
  brackets, like `["a", "b", "c"]`.
- **A "list comprehension"** — a compact way to build a new list by
  processing every item in an existing list in one line, instead of writing
  a longer, multi-line loop.

## The file path (line 4)

```python
CSV_PATH = os.path.join("static", "data", "skin_recommendations.csv")
```

This builds the location of the data file: `static/data/skin_recommendations.csv`.
`os.path.join(...)` is used instead of just writing that path as one string
by hand, because different operating systems use different characters to
separate folders (Windows uses `\`, Mac and Linux use `/`). Using
`os.path.join` means Python automatically uses whichever style is correct
for whatever computer the code happens to be running on, so the same code
works everywhere without changes.

## `_parse_product(entry)` — a small helper function

```python
def _parse_product(entry: str) -> dict:
    brand, _, name = entry.strip().partition("::")
    return {"brand": brand.strip(), "name": name.strip()}
```

Inside the CSV file, each recommended product is written in a specific
format, like this: `"CeraVe::Moisturizing Cream"` — the brand name, then two
colons `::`, then the product name. This function's whole job is to split
one of those strings apart into its two pieces.

`entry.strip()` first removes any accidental extra spaces from the very
start or end of the text. `.partition("::")` then splits the text into
exactly three parts around the first occurrence of `"::"`: everything
before it, the `"::"` itself, and everything after it. So
`"CeraVe::Moisturizing Cream"` becomes three separate values:
`"CeraVe"`, `"::"`, and `"Moisturizing Cream"`.

`brand, _, name = ...` assigns those three results to three variable names
in one line. The middle one is named `_` (a single underscore) — this is a
Python convention that means "I know a value goes here, but I'm
deliberately not going to use it," since the `"::"` separator itself isn't
needed for anything.

The function then returns a small dictionary: `{"brand": ..., "name": ...}`,
with `.strip()` applied again to each piece just in case there was extra
spacing directly around the `::`.

The underscore at the very start of the function's own name,
`_parse_product`, is a separate convention meaning "this function is only
meant to be used inside this file, as an internal helper — not something
other files should call directly."

## `get_recommendation(predicted_class)` — the main function

This is the one function `main.py` actually calls, passing in whatever
condition name the AI predicted (e.g. `"dark spots"`).

### Opening and reading the file

```python
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
```

`open(CSV_PATH, ...)` opens the CSV file for reading. `with ... as f:` is a
standard Python pattern (called a **context manager**) that guarantees the
file gets properly closed again automatically once this block of code
finishes — even if something goes wrong partway through — so there's no
need to remember to close it manually. `encoding="utf-8"` specifies exactly
how the text in the file should be interpreted, ensuring special characters
(like accented letters) are read correctly. `newline=""` is a small,
standard technical detail Python's own documentation recommends when
reading CSV files specifically, to avoid extra blank lines being introduced
by accident.

`csv.DictReader(f)` reads through the file one row at a time, and — this is
the useful part — automatically turns each row into a dictionary, using the
column headers from the very first line of the CSV file as the dictionary's
keys. So instead of having to remember "column number 3 is the explanation,"
the code can just ask for `row["explanation"]` by name, which is much
easier to read and far less likely to break if the columns were ever
reordered.

`for row in csv.DictReader(f):` loops through the file one row (one skin
condition) at a time, checking each one in turn.

### Finding the matching row

```python
if row["predicted_class"].lower() == predicted_class.lower():
```

For each row, this compares that row's `predicted_class` column against
whatever the AI actually predicted, passed into this function as the
`predicted_class` parameter. `.lower()` is applied to both sides before
comparing, converting everything to lowercase letters first — this makes
the comparison case-insensitive, so `"Dark Spots"`, `"dark spots"`, and
`"DARK SPOTS"` would all be treated as the same thing, avoiding a mismatch
just because of capitalization differences.

### Building the recommendation dictionary

```python
return {
    "concern_name": row["concern_name"],
    "explanation": row["explanation"],
    "ingredients": [i.strip() for i in row["ingredients"].split("|")],
    "suggested_products": [_parse_product(p) for p in row["suggested_products"].split("|")],
    "skincare_advice": [a.strip() for a in row["skincare_advice"].split("|")],
}
```

Once a matching row is found, this builds and immediately returns the final
dictionary of recommendation data. `concern_name` and `explanation` are
copied over directly, since they're just single pieces of text with nothing
extra to process.

`ingredients` and `skincare_advice`, however, each hold *multiple* items
packed into a single spreadsheet cell, separated by the `|` (pipe)
character — for example, `"Niacinamide|Salicylic Acid|Zinc"`. The code
`[i.strip() for i in row["ingredients"].split("|")]` is a list
comprehension: `.split("|")` first breaks that one long string apart into a
list of separate pieces wherever a `|` appears, then `i.strip()` removes any
stray extra spaces around each individual piece, and the whole thing is
collected into a fresh, clean list. `skincare_advice` works exactly the
same way.

`suggested_products` does something similar, but each individual item also
needs the brand/name splitting handled by `_parse_product` (explained
above): `.split("|")` first breaks the cell into a list of raw
`"Brand::Name"` strings, and then `_parse_product(p) for p in ...` runs
each one through that helper function, turning every raw string into a
proper `{"brand": ..., "name": ...}` dictionary.

Because this whole block is a `return` statement, as soon as the first
matching row is found and this dictionary is built, the function
immediately stops and hands this result back — it doesn't keep checking any
remaining rows in the file.

### If nothing matched

```python
return {
    "concern_name": predicted_class,
    "explanation": "No recommendation data found for this condition.",
    "ingredients": [],
    "suggested_products": [],
    "skincare_advice": [],
}
```

This line only runs if the `for` loop above finished checking every single
row in the file *without* ever finding a match (normally this shouldn't
happen, since every one of the 8 possible AI predictions has a
corresponding row in the CSV file — but it's good practice to handle the
case anyway). Rather than letting the program crash with a confusing error,
it returns a safe, harmless "fallback" dictionary: the condition's own name,
a plain explanation that no data was found, and empty lists (`[]` — a list
with nothing in it) for ingredients, products, and advice. Because this
fallback has exactly the same shape (the same dictionary keys) as a real
recommendation, whatever code displays this data later (`result.html`)
doesn't need any special-case handling for "what if nothing was found" — it
can just display an empty list of ingredients the same way it would display
a full one.
