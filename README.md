# bhushan_profile_webport

My personal résumé site, written in blue ink on a ruled exam answer sheet, laid out like a classic résumé
(objective, experience, skills, qualifications table, declaration).
Live at **https://bhushanladde02.github.io/bhushan_profile_webport/** once GitHub Pages is on (see below).

All content lives in one file, `content/profile.json`. A small Python script (standard library only)
renders it into a static site in `docs/`, which GitHub Pages serves.

## Layout

```
content/profile.json   ← edit this: objective, roles, projects, skills, education, awards
assets/headshot.jpg    ← profile photo (passport-style, pasted top right)
templates/index.html   ← page structure with {{PLACEHOLDERS}}
static/style.css       ← answer-sheet look: ruled lines, red margin, blue ink
static/fonts/          ← Kalam and Caveat handwriting fonts, self-hosted
webport/build.py       ← renders the site (no JavaScript in the output)
docs/                  ← generated site, committed, served by GitHub Pages
tests/                 ← pytest checks on the generated page
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
- Roles can be listed in any order; Work Experience is always printed newest first, sorted by `start`
  (`YYYY-MM`). `dates` is the text shown to readers.
- In `pitch` and `achievements`, wrap a phrase in `[[double brackets]]` to underline it.
- `education` rows fill the qualifications table; leave `result` empty to print a dash.
- A project with `"done": false` gets an empty checkbox; add `"url"` to link it.

## Keeping writing on the lines

The paper is ruled every 32px. Every line of text is exactly 32px tall (headings 64px) and every gap is a
multiple of 32px, so text never drifts off the lines. If you add styles, keep to that: no top/bottom
borders, margins or padding that are not multiples of 32px. Draw decorative lines with `box-shadow`,
which takes no space. Kalam's baseline sits 20px into each line, so text is nudged down 9px visually
(`position: relative; top`) to rest on the rule.

## Publishing on GitHub Pages

1. Push this repo to `github.com/bhushanladde02/bhushan_profile_webport` (public).
2. Repo **Settings → Pages → Build and deployment**: Source *Deploy from a branch*, Branch `main`, folder `/docs`, **Save**.
3. The site appears at `https://bhushanladde02.github.io/bhushan_profile_webport/`.

The `test` workflow in `.github/workflows/` runs the tests on every push and fails if `docs/` was not rebuilt
after a content change.

To use the shorter address `https://bhushanladde02.github.io`, create a repo named
`bhushanladde02.github.io` and copy the contents of `docs/` into it. For a custom domain, add it under
Settings → Pages → Custom domain and point the domain's DNS at GitHub Pages.

## Credits

Design and code were drafted with AI assistance (Claude). Content, review and testing are my own.

Fonts: [Kalam](https://fonts.google.com/specimen/Kalam) and [Caveat](https://fonts.google.com/specimen/Caveat),
both under the SIL Open Font License, via Fontsource.
