"""Render content/profile.json into a page-turning notebook site in docs/ (served by GitHub Pages)."""

from __future__ import annotations

import base64
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "profile.json"
TEMPLATE = ROOT / "templates" / "index.html"
STATIC = ROOT / "static"
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"

REQUIRED = ["name", "headline", "updated", "pitch", "email", "linkedin", "github", "photo", "roles"]
TOKEN = re.compile(r"^[a-z0-9-]+$")  # page ids used in the URL (#nielsen)


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def month_value(ym: str) -> float:
    """'2022-03' -> 2022.1667, used to sort roles."""
    year, month = ym.split("-")
    return int(year) + (int(month) - 1) / 12


def render_pitch(text: str) -> str:
    """Escape text, then turn [[phrase]] into an underlined <mark>."""
    return re.sub(r"\[\[(.+?)\]\]", r"<mark>\1</mark>", esc(text))


def prepare_roles(roles: list[dict]) -> list[dict]:
    """Return roles newest first, with numeric from/to and a short year range."""
    out = []
    for r in roles:
        start, end = month_value(r["start"]), month_value(r["end"])
        if end <= start:
            raise ValueError(f"role {r['id']!r} ends before it starts")
        item = dict(r)
        item["from"], item["to"] = round(start, 4), round(end, 4)
        item["years"] = f"{r['start'][:4]}–{r['end'][2:4]}"
        out.append(item)
    out.sort(key=lambda r: r["from"], reverse=True)
    return out


def short_url(url: str) -> str:
    return url.split("://", 1)[-1].rstrip("/")


def bullets(items, fmt=esc) -> str:
    return '<ul class="pts">' + "".join(f"<li>{fmt(x)}</li>" for x in items) + "</ul>"


# ---------- page bodies ----------

def cover_lead(p: dict, photo: str) -> str:
    """Top of the index page: photo pasted in, name and how to reach me."""
    return (f'<div class="lead"><img class="photo" src="{photo}" alt="{esc(p["name"])}" width="118" height="148">'
            f'<h1 class="name">{esc(p["name"])}</h1>'
            f'<p>{headline_html(p["headline"])}</p>'
            f'<p>{esc(p.get("location", ""))}</p>'
            f'<p><a href="mailto:{esc(p["email"])}">{esc(p["email"])}</a>'
            + (f' · <a href="tel:{esc(re.sub(r"[^0-9+]", "", p["phone"]))}">{esc(p["phone"])}</a>' if p.get("phone") else "")
            + '</p>'
            f'<p><a href="{esc(p["linkedin"])}" target="_blank" rel="noopener">{esc(short_url(p["linkedin"]))}</a> · '
            f'<a href="{esc(p["github"])}" target="_blank" rel="noopener">{esc(short_url(p["github"]))}</a></p>'
            + work_auth(p) + download_link(p) + '</div>')


def headline_html(headline: str) -> str:
    """Role first; the specialty after ' · ' is dropped on phones to save lines."""
    role, sep, rest = headline.partition(" · ")
    return esc(role) + (f'<span class="hl-rest"> · {esc(rest)}</span>' if sep else "")


def download_link(p: dict) -> str:
    pdf = p.get("resume_pdf")
    if not pdf:
        return ""
    return (f'<p class="dl"><a href="{esc(pdf)}" download target="_blank" rel="noopener">'
            f'↓ Download résumé (PDF)</a></p>')


def work_auth(p: dict) -> str:
    """Visa line as a rubber stamp: the status, then the fact that makes it easy."""
    w = p.get("work_authorization")
    if not w:
        return ""
    return (f'<p class="visa"><span class="stamp">{esc(w["status"])}</span> '
            f'<span class="visa-note">{esc(w.get("note", ""))}</span></p>')


def about_body(p: dict) -> str:
    return (
        f'<h3>Career Objective :-</h3><p class="para">{esc(p.get("objective", ""))}</p>'
        f'<div class="gap"></div><h3>Professional Summary :-</h3>{bullets(p.get("summary", []), render_pitch)}'
        + (f'<div class="gap"></div><h3>Highlights :-</h3>{highlights_body(p)}' if p.get("highlights") else "")
    )


def highlights_body(p: dict) -> str:
    cells = "".join(f'<div class="stat"><b>{esc(h["figure"])}</b><span>{esc(h["text"])}</span></div>'
                    for h in p.get("highlights", []))
    return f'<div class="stats">{cells}</div>'


def role_block(r: dict) -> str:
    company = r.get("company") or r["org"]
    return (f'<article class="role" id="role-{r["id"]}">'
            f'<h3><span>{esc(r["title"])}<span class="co">, {esc(company)}</span></span><span class="when">{esc(r["dates"])}</span></h3>'
            f'{bullets(r["points"])}'
            f'<p class="tech">Stack: {esc(r["stack"])}</p></article>')


def experience_body(p: dict) -> str:
    return "".join(role_block(r) for r in prepare_roles(p["roles"]))


def projects_body(p: dict) -> str:
    rows = []
    for x in p.get("projects", []):
        box = '<span class="box done" aria-label="Done"></span>' if x.get("done") else '<span class="box" aria-label="In progress"></span>'
        status = esc(x.get("status", ""))
        if x.get("url"):
            status += f', <a href="{esc(x["url"])}" target="_blank" rel="noopener">{esc(short_url(x["url"]))}</a>'
        rows.append(f'<li>{box}<b>{esc(x["name"])}</b> ({status}) – {esc(x["text"])} '
                    f'<span class="tech">[{esc(x["stack"])}]</span></li>')
    return '<ul class="projects">' + "".join(rows) + "</ul>"


def skills_body(p: dict) -> str:
    return '<dl class="kv">' + "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in p.get("skills", [])) + "</dl>"


def education_body(p: dict) -> str:
    head = "".join(f'<span role="columnheader"><i>{h}</i></span>' for h in ["Qualification", "University / College", "Year", "Result"])
    rows = "".join(
        '<div class="edu-row" role="row">' + "".join(f'<span role="cell"><i>{esc(c)}</i></span>'
        for c in [e["degree"], e["school"], e["year"], e.get("result") or "—"]) + "</div>"
        for e in p.get("education", []))
    return (f'<div class="table-wrap"><div class="edu" role="table" aria-label="Educational qualifications">'
            f'<div class="edu-row edu-head" role="row">{head}</div>{rows}</div></div>')


def awards_body(p: dict) -> str:
    return bullets(p.get("awards", []), lambda a: esc(a[0]) + (f" ({esc(a[1])})" if a[1] else ""))


def cover_note_body(p: dict) -> str:
    n = p["cover_note"]
    paras = "".join(f'<p class="para">{esc(t)}</p>' for t in n.get("paragraphs", []))
    return (f'<p>{esc(n.get("greeting", ""))}</p>{paras}'
            f'<div class="gap"></div><h3>{esc(n.get("bring_title", ""))}</h3>{bullets(n.get("bring", []))}'
            f'<div class="gap"></div><p class="para">{esc(n.get("closing", ""))}</p>'
            f'<div class="note-sign"><p>{esc(n.get("signoff", ""))}</p><p class="scrawl">{esc(p["name"])}</p></div>')


def declaration_body(p: dict) -> str:
    place = p.get("location", "").split(",")[0]
    return (f'<p class="para">{esc(p.get("declaration", ""))}</p><div class="gap"></div><div class="gap"></div>'
            f'<div class="sign"><div><p>Place: {esc(place)}</p><p>Date: <span class="js-date">{esc(p["updated"])}</span></p></div>'
            f'<div class="sig"><p class="scrawl">{esc(p["name"])}</p><p>({esc(p["name"])})</p></div></div>')


# ---------- the notebook ----------

def build_pages(p: dict, photo: str) -> list[dict]:
    """Page 0 is the index; then one complete page per section, numbered 1..n."""
    roles = prepare_roles(p["roles"])
    span = f'{roles[-1]["start"][:4]}–{roles[0]["end"][2:4]}'
    edu_body = education_body(p) + '<div class="gap"></div><h3>Awards &amp; Certifications</h3>' + awards_body(p) \
        + '<div class="gap"></div><h3>Declaration</h3>' + declaration_body(p)
    pages = [
        {"token": "index", "title": "Index", "date": "", "body": None, "lead": cover_lead(p, photo)},
        {"token": "about", "title": "About Me", "date": p["updated"], "body": about_body(p)},
        {"token": "experience", "title": "Work Experience", "date": span, "body": experience_body(p),
         "parts": [(r["label"], r["title"], f'role-{r["id"]}', r["years"]) for r in roles]},
        {"token": "projects", "title": "Projects", "date": p["updated"], "body": projects_body(p)},
        {"token": "skills", "title": "Technical Skills", "date": p["updated"], "body": skills_body(p)},
        {"token": "education", "title": "Education & Awards", "date": p["updated"], "body": edu_body},
    ]
    if p.get("cover_note"):
        pages.append({"token": "note", "title": p["cover_note"].get("title", "Cover Note"),
                      "date": p["updated"], "body": cover_note_body(p)})
    seen = set()
    for n, page in enumerate(pages):
        page["number"] = n
        if not TOKEN.match(page["token"]) or page["token"] in seen:
            raise ValueError(f"bad or duplicate page id: {page['token']!r}")
        seen.add(page["token"])
    for r in roles:
        if not TOKEN.match(r["id"]):
            raise ValueError(f"bad role id: {r['id']!r}")
    return pages


def index_body(pages: list[dict], updated: str = "") -> str:
    def row(sr, text, goto, anchor, page_no, date, cls="", extra=""):
        href = f"#{anchor or pages[goto]['token']}"
        more = f'<i class="lg"> · {esc(extra)}</i>' if extra else ""
        return (f'<a class="idx-row{cls}" href="{href}">'
                f'<span>{sr}</span><span>{esc(text)}{more}</span><span class="pno">{page_no}</span>'
                + (f'<span class="js-date">{esc(date)}</span></a>' if date == updated else f'<span>{esc(date)}</span></a>'))

    rows = []
    for pg in pages[1:]:
        rows.append(row(f'{pg["number"]}.', pg["title"], pg["number"], "", pg["number"], pg["date"]))
        for k, (label, title, anchor, date) in enumerate(pg.get("parts", [])):
            rows.append(row(f'({chr(97 + k)})', label, pg["number"], anchor, pg["number"], date, " idx-sub", title))
    head = ('<div class="idx-row idx-head" aria-hidden="true">'
            '<span><i class="lg">Sr. No.</i><i class="sh">No.</i></span><span>Contents</span>'
            '<span><i class="lg">Page No.</i><i class="sh">Page</i></span><span>Date</span></div>')
    return f'<nav class="idx" aria-label="Index">{head}<div class="idx-body">{"".join(rows)}</div></nav>'


def render_page(pg: dict, pages: list[dict], fallback_date: str = "") -> str:
    n = pg["number"]
    corner_no = "Index" if n == 0 else str(n)
    heading = "INDEX" if n == 0 else esc(pg["title"])
    links = []
    if n > 0:
        prev = pages[n - 1]
        links.append(f'<a class="prev" href="#{prev["token"]}">↑ {esc(prev["title"])}</a>')
    if n + 1 < len(pages):
        nxt = pages[n + 1]
        links.append(f'<a class="next" href="#{nxt["token"]}">Next: {esc(nxt["title"])} ↓</a>')
    foot = f'<div class="gap"></div><nav class="turn" aria-label="Sections">{"".join(links)}</nav>'
    return (
        f'    <section class="page" id="{pg["token"]}" data-token="{pg["token"]}" data-title="{esc(pg["title"])}" '
        f'aria-label="{esc(pg["title"])}">\n'
        f'      <div class="corner"><span class="lbl">Page No.</span><span class="val">{corner_no}</span>'
        f'<span class="lbl">Date</span><span class="val js-date">{esc(fallback_date)}</span></div>\n'
        + (f'      {pg["lead"]}\n' if pg.get("lead") else "")
        + f'      <h2>{heading}</h2>\n'
        f'      {pg["body"]}\n'
        f'      {foot}\n'
        f'    </section>'
    )


def tabs_html(pages: list[dict], p: dict) -> str:
    """The strip of section tabs that stays at the top while you scroll."""
    short = {"index": "Index", "about": "About", "experience": "Experience", "projects": "Projects",
             "skills": "Skills", "education": "Education", "note": "Note"}
    links = [f'    <a href="#{pg["token"]}" data-tab="{pg["token"]}">{esc(short.get(pg["token"], pg["title"]))}</a>'
             for pg in pages]
    if p.get("resume_pdf"):
        links.append(f'    <a class="tab-pdf" href="{esc(p["resume_pdf"])}" download target="_blank" rel="noopener">↓ PDF</a>')
    return "\n".join(links)


def render(profile: dict, *, inline: bool = False) -> str:
    missing = [k for k in REQUIRED if not profile.get(k)]
    if missing:
        raise ValueError(f"profile.json is missing: {', '.join(missing)}")

    css = (STATIC / "style.css").read_text(encoding="utf-8")
    js = (STATIC / "notebook.js").read_text(encoding="utf-8")
    photo_path = ASSETS / profile["photo"]
    if inline:
        css = re.sub(r"url\(fonts/([\w.-]+)\)", lambda m: "url(data:font/woff2;base64," + base64.b64encode(
            (STATIC / "fonts" / m.group(1)).read_bytes()).decode() + ")", css)
        style, script = f"<style>\n{css}</style>", f"<script>\n{js}</script>"
        photo = "data:image/jpeg;base64," + base64.b64encode(photo_path.read_bytes()).decode()
    else:
        style, script = '<link rel="stylesheet" href="style.css">', '<script src="notebook.js"></script>'
        photo = esc(profile["photo"])

    pages = build_pages(profile, photo)
    pages[0]["body"] = index_body(pages, profile["updated"])
    html_pages = "\n".join(render_page(pg, pages, profile["updated"]) for pg in pages)

    values = {
        "NAME": esc(profile["name"]),
        "HEADLINE": esc(profile["headline"]),
        "UPDATED": esc(profile["updated"]),
        "PAGES": html_pages,
        "TABS": tabs_html(pages, profile),
        "STYLE": style,
        "SCRIPT": script,
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], page)


def load_profile(path: Path = CONTENT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build(out_dir: Path = DOCS) -> Path:
    """Write index.html, style.css, notebook.js, fonts and the photo into out_dir."""
    profile = load_profile()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render(profile), encoding="utf-8")
    shutil.copyfile(STATIC / "style.css", out_dir / "style.css")
    shutil.copyfile(STATIC / "notebook.js", out_dir / "notebook.js")
    shutil.copytree(STATIC / "fonts", out_dir / "fonts", dirs_exist_ok=True)
    shutil.copyfile(ASSETS / profile["photo"], out_dir / profile["photo"])
    if profile.get("resume_pdf"):
        shutil.copyfile(ASSETS / profile["resume_pdf"], out_dir / profile["resume_pdf"])
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    return out_dir / "index.html"


def build_single_file(out_file: Path) -> Path:
    """One self-contained HTML file (CSS, script, fonts and photo embedded)."""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(render(load_profile(), inline=True), encoding="utf-8")
    return out_file
