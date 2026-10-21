"""Render content/profile.json into a static site in docs/ (served by GitHub Pages)."""

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


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def month_value(ym: str) -> float:
    """'2022-03' -> 2022.1667 (fractional year), used to size timeline blocks."""
    year, month = ym.split("-")
    return int(year) + (int(month) - 1) / 12


def render_pitch(pitch: str) -> str:
    """Escape the pitch, then turn [[phrase]] into a highlighted <mark>."""
    return re.sub(r"\[\[(.+?)\]\]", r"<mark>\1</mark>", esc(pitch))


def prepare_roles(roles: list[dict]) -> list[dict]:
    """Return roles newest first, with numeric from/to and a year-range label."""
    out = []
    for r in roles:
        start, end = month_value(r["start"]), month_value(r["end"])
        if end <= start:
            raise ValueError(f"role {r['id']!r} ends before it starts")
        item = dict(r)
        item["from"], item["to"] = round(start, 4), round(end, 4)
        item["years"] = f"{r['start'][:4]}–{r['end'][:4]}"
        out.append(item)
    out.sort(key=lambda r: r["from"], reverse=True)
    return out


def short_url(url: str) -> str:
    return url.split("://", 1)[-1].rstrip("/")


def render_job(r: dict) -> str:
    points = "\n".join(f"        <li>{esc(p)}</li>" for p in r["points"])
    return (
        f'    <article class="job">\n'
        f'      <div class="job-top"><b>{esc(r["title"])}</b><span class="when">{esc(r["dates"])}</span></div>\n'
        f'      <p class="org">{esc(r["org"])}</p>\n'
        f'      <ul>\n{points}\n      </ul>\n'
        f'      <p class="tech">Environment: {esc(r["stack"])}</p>\n'
        f'    </article>'
    )


def render_project(p: dict) -> str:
    status = esc(p.get("status", ""))
    if p.get("url"):
        status += f', <a href="{esc(p["url"])}" target="_blank" rel="noopener">{esc(short_url(p["url"]))}</a>'
    return (f'      <li><b>{esc(p["name"])}</b> ({status}) – {esc(p["text"])} '
            f'<span class="stack">[{esc(p["stack"])}]</span></li>')


def render_education(e: dict) -> str:
    cells = [e["degree"], e["school"], e["year"], e.get("result") or "—"]
    return '        <div class="tr" role="row">' + "".join(
        f'<span role="cell"><i>{esc(c)}</i></span>' for c in cells) + "</div>"


def render(profile: dict, *, inline: bool = False) -> str:
    missing = [k for k in REQUIRED if not profile.get(k)]
    if missing:
        raise ValueError(f"profile.json is missing: {', '.join(missing)}")

    roles = prepare_roles(profile["roles"])
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    photo_path = ASSETS / profile["photo"]
    if inline:
        css = re.sub(r"url\(fonts/([\w.-]+)\)", lambda m: "url(data:font/woff2;base64," + base64.b64encode((STATIC / "fonts" / m.group(1)).read_bytes()).decode() + ")", css)
        style = f"<style>\n{css}</style>"
        photo = "data:image/jpeg;base64," + base64.b64encode(photo_path.read_bytes()).decode()
    else:
        style = '<link rel="stylesheet" href="style.css">'
        photo = esc(profile["photo"])

    def award(a):
        name, year = a
        return f"      <li>{esc(name)}" + (f" ({esc(year)})" if year else "") + "</li>"

    values = {
        "NAME": esc(profile["name"]),
        "HEADLINE": esc(profile["headline"]),
        "LOCATION": esc(profile.get("location", "")),
        "UPDATED": esc(profile["updated"]),
        "PLACE": esc(profile.get("location", "").split(",")[0]),
        "SIGNATURE": esc(profile["name"]),
        "OBJECTIVE": esc(profile.get("objective", "")),
        "PITCH": render_pitch(profile["pitch"]),
        "ACHIEVEMENTS": "\n".join(f"      <li>{render_pitch(a)}</li>" for a in profile.get("achievements", [])),
        "EXPERIENCE": "\n".join(render_job(r) for r in roles),
        "PROJECTS": "\n".join(render_project(p) for p in profile.get("projects", [])),
        "SKILLS": "\n".join(f"      <dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in profile.get("skills", [])),
        "EDUCATION": "\n".join(render_education(e) for e in profile.get("education", [])),
        "AWARDS": "\n".join(award(a) for a in profile.get("awards", [])),
        "DECLARATION": esc(profile.get("declaration", "")),
        "EMAIL": esc(profile["email"]),
        "LINKEDIN": esc(profile["linkedin"]),
        "LINKEDIN_SHORT": esc(short_url(profile["linkedin"])),
        "GITHUB": esc(profile["github"]),
        "GITHUB_SHORT": esc(short_url(profile["github"])),
        "PHOTO": photo,
        "STYLE": style,
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], page)


def load_profile(path: Path = CONTENT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build(out_dir: Path = DOCS) -> Path:
    """Write index.html, style.css and the photo into out_dir."""
    profile = load_profile()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render(profile), encoding="utf-8")
    shutil.copyfile(STATIC / "style.css", out_dir / "style.css")
    shutil.copytree(STATIC / "fonts", out_dir / "fonts", dirs_exist_ok=True)
    shutil.copyfile(ASSETS / profile["photo"], out_dir / profile["photo"])
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    return out_dir / "index.html"


def build_single_file(out_file: Path) -> Path:
    """One self-contained HTML file (CSS and photo embedded), handy for sharing."""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(render(load_profile(), inline=True), encoding="utf-8")
    return out_file
