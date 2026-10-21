# bhushan.ladde

My résumé as an old-school notebook: white ruled pages written in blue ink, a red margin, a cloth
binding down the left edge, and an index at the front.
Live at **https://bhushanladde02.github.io/bhushan.ladde/**

All content lives in one file, `content/profile.json`. A small Python script (standard library only)
renders it into a static site in `docs/`, which GitHub Pages serves.

## What's in the notebook

Five sections after the index. Every page is the same size and nothing scrolls: when a section has more
writing than one page holds, it carries over to the next page under "(contd.)", the way you would write
in a real notebook. A job is never split across pages, and a heading is never left alone at the foot
of a page.

| Section | Contents |
|---------|----------|
| Index | My photo, name, title and contact details, then Sr. No., contents, page numbers and dates |
| About Me | Career objective, professional summary, highlights |
| Work Experience | Every role, newest first, each with a one-line heading and its strongest points |
| Projects | Live and in-progress projects with a tick box for each |
| Technical Skills | Grouped skills |
| Education & Awards | Qualifications table, awards, and the signed declaration |

On a laptop the notebook lies open, showing two facing pages with the binding down the middle (about
4–5 views in all); on a phone it shows one page at a time. Page numbers in each corner and in the index
follow how the pages actually fall on that screen.

Reading it: the bar under the pages always names what comes next ("Next: Work Experience →"); the
← / → keys and a swipe on phones do the same, and each index row opens its page. Every section has its
own link, e.g. `…/bhushan.ladde/#projects`, and each job too, e.g. `#role-nielsen`.
Without JavaScript the sections simply stack down the screen.

## Layout

```
content/profile.json   ← edit this: everything written in the notebook
assets/headshot.jpg    ← profile photo (pasted at the top of the Index page)
templates/index.html   ← the notebook shell: binding and pages
static/style.css       ← binding, ruled pages, red margin, blue ink, two-page spread
static/notebook.js     ← flows sections onto equal pages, spreads, live page numbers, next bar, keys, swipe
static/fonts/          ← Kalam and Caveat handwriting fonts, self-hosted
webport/build.py       ← builds the pages and the index from profile.json
docs/                  ← generated site, committed, served by GitHub Pages
tests/                 ← pytest checks on the generated notebook
```

## Everyday commands

Requires Python 3.9+. No dependencies except `pytest` for the tests.

```bash
python3 -m webport build          # render content into docs/
python3 -m webport serve          # build, then preview at http://localhost:8000
python3 -m webport single         # one self-contained file at dist/bhushan-ladde.html
python3 -m pip install pytest && python3 -m pytest -q   # run the tests
```

## Updating the site

1. Edit `content/profile.json` (or swap `assets/headshot.jpg`).
2. `python3 -m webport build`
3. `python3 -m pytest -q`
4. Commit both your change and the regenerated `docs/`, then push. Pages redeploys in about a minute.

Notes on `profile.json`:
- Sections and the index are generated; adding a role adds it to Work Experience.
- Roles can be listed in any order; they are printed newest first, sorted by `start` (`YYYY-MM`).
  `dates` is the text shown to readers. A role's `id` becomes its link (`#role-<id>`), so use lowercase
  letters, digits and dashes. `company` is shown after the title on the role's heading line.
  Keep each role to its strongest 2–6 points, each short enough for one line; that is what keeps the
  whole notebook to a few spreads.
- In `pitch` and `summary`, wrap a phrase in `[[double brackets]]` to underline it.
- `highlights` are the big handwritten numbers at the end of the About page.
- `education` rows fill the qualifications table; leave `result` empty to print a dash.
- A project with `"done": false` gets an empty checkbox; add `"url"` to link it.

## Keeping writing on the lines

The paper is ruled every 28px (`--u` in `static/style.css`). Every line of text is exactly one rule tall
(headings two) and every gap is a whole number of rules, so text never drifts off the lines. If you add
styles, keep to that: no top/bottom borders, margins or padding that are not multiples of `--u`. Draw
decorative lines with `box-shadow`, which takes no space.

Each size of handwriting has a measured nudge (`--n1`, `--n-h2`, `--n-name` and so on in `:root`) that
moves it down onto its rule without changing the layout. If you change `--u` or a font size, re-measure
those values.

Pages are a whole number of lines that fits the window (between 16 and 30, worked out in
`static/notebook.js`), so every page has the same rows. Wide windows (1100px and up) show two pages.

## Publishing on GitHub Pages

The repo is `github.com/bhushanladde02/bhushan.ladde` (public). Pages is set to **Deploy from a branch**,
branch `main`, folder `/docs`. The site is at `https://bhushanladde02.github.io/bhushan.ladde/`.

The `test` workflow in `.github/workflows/` runs the tests on every push and fails if `docs/` was not rebuilt
after a content change.

For a custom domain, add it under Settings → Pages → Custom domain and point the domain's DNS at GitHub Pages.

## Credits

Design and code were drafted with AI assistance (Claude). Content, review and testing are my own.

Fonts: [Kalam](https://fonts.google.com/specimen/Kalam) and [Caveat](https://fonts.google.com/specimen/Caveat),
both under the SIL Open Font License, via Fontsource.
