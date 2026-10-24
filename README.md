# bhushan.ladde

My résumé as an old-school notebook on one scrolling page: white ruled sheets written in blue ink, a red
margin, a spiral wire binding down the left edge, and an index at the front.
Live at **https://bhushanladde02.github.io/bhushan.ladde/**

All content lives in one file, `content/profile.json`. A small Python script (standard library only)
renders it into a static site in `docs/`, which GitHub Pages serves.

## What's in the notebook

Seven sheets stacked down one page, the index first, with a thin seam between sheets. Each sheet is as
long as its writing. The spiral binding has one silver loop through a punched hole on every ruled line
(an inline SVG tile, 44×28px, on `.binding` in `static/style.css`).

| Section | Contents |
|---------|----------|
| Index | My photo, name, title, contact details (email, phone, LinkedIn, GitHub), a work-authorization stamp (`work_authorization` in `profile.json`) and a link to download my PDF résumé, then Sr. No., contents (with a row per job), page numbers and dates |
| About Me | Career objective, professional summary, highlights |
| Work Experience | Every role, newest first, each with a one-line heading and its strongest points |
| Projects | Live and in-progress projects with a tick box for each |
| Technical Skills | Grouped skills |
| Education & Awards | Qualifications table, awards, and the signed declaration |
| Cover Note | A short, signed note to the hiring manager: what I bring (`cover_note` in `profile.json`) |

Getting around:
- A strip of section tabs (Index, About, Experience, Projects, Skills, Education, Note, ↓ PDF) stays at
  the top while you scroll. The tab for the sheet you are reading is filled in, and a thin line under the
  tabs fills up as you read down the page.
- Every index row, including each job, scrolls smoothly to its place; the sheet you land on flashes briefly.
- Each sheet ends with "Next: … ↓" and "↑ …" links, and an "↑ Index" button appears once you scroll down.
- Every sheet and job has its own link, e.g. `…/bhushan.ladde/#projects` or `#role-nielsen`.
- Section headings draw their ink underline as they scroll into view (skipped for readers who turn
  off motion). Without JavaScript everything still works as plain links.

Dates: the Date box on every page (and the declaration) always shows yesterday's date, worked out from
the visitor's clock when the page opens (`.js-date` in the HTML, filled by `static/notebook.js`). The build
writes the `updated` month there as a fallback for readers without JavaScript.


## Layout

```
content/profile.json   ← edit this: everything written in the notebook
assets/headshot.jpg    ← profile photo (pasted at the top of the Index page)
assets/Bhushan_Ladde_Resume.pdf ← downloadable résumé; swap the file to update it (`resume_pdf` in profile.json)
templates/index.html   ← the shell: section tabs, spiral binding, sheets, back-to-top button
static/style.css       ← spiral binding, ruled sheets, red margin, blue ink, tabs
static/notebook.js     ← yesterday's dates, smooth scrolling, active tab, reading progress, ink underlines
static/fonts/          ← Kalam and Caveat handwriting fonts, self-hosted
webport/build.py       ← builds the sheets, index and tabs from profile.json
docs/                  ← generated site, committed, served by GitHub Pages
tests/                 ← pytest checks on the generated notebook.
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
  Keep each role to its strongest 2–6 points, each short enough for one line.
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

Each sheet's height is a whole number of lines because everything on it is.

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
