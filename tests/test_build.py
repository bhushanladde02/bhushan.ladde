import re
from html.parser import HTMLParser

import pytest

from webport import build as b


@pytest.fixture(scope="module")
def profile():
    return b.load_profile()


@pytest.fixture(scope="module")
def page(profile):
    return b.render(profile)


@pytest.fixture(scope="module")
def pages(profile):
    return b.build_pages(profile, "headshot.jpg")


def tokens(html):
    return re.findall(r'data-token="([^"]+)"', html)


def test_no_unfilled_placeholders(page):
    assert "{{" not in page and "}}" not in page


def test_html_parses_and_tags_balance(page):
    stack = []
    void = {"meta", "link", "img", "br", "input", "hr"}

    class P(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag not in void:
                stack.append(tag)

        def handle_endtag(self, tag):
            assert stack and stack[-1] == tag, f"unexpected </{tag}>"
            stack.pop()

    P().feed(page)
    assert stack == []


def test_notebook_opens_on_the_index_then_section_pages(page):
    assert tokens(page) == ["index", "about", "experience", "projects", "skills", "education", "note"]


def test_index_lists_every_section_and_job(page, pages, profile):
    rows = re.findall(r'<a class="idx-row" href="#([a-z0-9-]+)"', page)
    assert rows == [pg["token"] for pg in pages[1:]]
    jobs = re.findall(r'<a class="idx-row idx-sub" href="#([a-z0-9-]+)"', page)
    assert jobs == [f"role-{r['id']}" for r in b.prepare_roles(profile["roles"])]


def test_sticky_tabs_link_every_sheet_and_the_pdf(page, pages, profile):
    tabs = re.findall(r'<a href="#([a-z0-9-]+)" data-tab="\1">', page)
    assert tabs == [pg["token"] for pg in pages]
    assert f'class="tab-pdf" href="{profile["resume_pdf"]}" download' in page


def test_one_scrolling_page_no_pagination(page):
    js = (b.STATIC / "notebook.js").read_text(encoding="utf-8")
    assert "paginate" not in js and "bar-next" not in page
    for pg_id in ["index", "about", "experience", "projects", "skills", "education", "note"]:
        assert f'<section class="page" id="{pg_id}"' in page


def test_every_role_has_a_link_target(page, profile):
    for r in profile["roles"]:
        assert page.count(f'id="role-{r["id"]}"') == 1


def test_role_heading_is_one_line_with_company(page, profile):
    nielsen = next(r for r in profile["roles"] if r["id"] == "nielsen")
    assert f'{nielsen["title"]}<span class="co">, {nielsen["company"]}</span>' in page


def test_each_page_names_the_next_page(page, pages):
    nexts = re.findall(r'class="next"[^>]*>Next: ([^<]+) ↓</a>', page)
    assert nexts == [b.esc(pg["title"]) for pg in pages[1:]]


def test_index_has_no_remarks_column(page):
    assert "Remarks" not in page and "class=\"tick\"" not in page


def test_experience_is_one_page_latest_first(page, profile):
    order = re.findall(r'<article class="role" id="role-([a-z0-9-]+)"', page)
    assert order[0] == "nielsen" and order[-1] == "sne"
    assert len(order) == len(profile["roles"])
    starts = [r["from"] for r in b.prepare_roles(profile["roles"])]
    assert starts == sorted(starts, reverse=True)


def test_nielsen_stack_leads_with_python(profile):
    nielsen = next(r for r in profile["roles"] if r["id"] == "nielsen")
    assert nielsen["stack"].split(",")[0].strip() == "Python"


def test_page_numbers_in_corner_match_order(page):
    corners = re.findall(r'<span class="lbl">Page No\.</span><span class="val">([^<]+)</span>', page)
    assert corners[0] == "Index"
    assert corners[1:] == [str(n) for n in range(1, len(corners))]


def test_bad_role_ids_are_rejected(profile):
    broken = dict(profile)
    broken["roles"] = [dict(profile["roles"][0], id="Bad ID")]
    with pytest.raises(ValueError, match="role id"):
        b.build_pages(broken, "x.jpg")


def test_highlight_and_escaping():
    assert b.render_pitch("a [[b & c]] d") == "a <mark>b &amp; c</mark> d"
    assert "<script>" not in b.render_pitch("<script>x</script>")


def test_role_end_before_start_is_rejected():
    with pytest.raises(ValueError):
        b.prepare_roles([{"id": "x", "start": "2020-05", "end": "2020-01"}])


def test_missing_field_is_reported(profile):
    broken = dict(profile)
    del broken["email"]
    with pytest.raises(ValueError, match="email"):
        b.render(broken)


def test_all_content_appears(page, profile):
    for p in profile["projects"]:
        assert b.esc(p["name"]) in page
    for name, _ in profile["skills"]:
        assert b.esc(name) in page
    for e in profile["education"]:
        assert b.esc(e["school"]) in page
    for r in profile["roles"]:
        for point in r["points"]:
            assert b.esc(point) in page


def test_build_writes_site(tmp_path):
    index = b.build(tmp_path)
    for name in ["index.html", "style.css", "notebook.js", "headshot.jpg", ".nojekyll", "Bhushan_Ladde_Resume.pdf",
                 "fonts/kalam-latin-300-normal.woff2"]:
        assert (tmp_path / name).exists(), name
    text = index.read_text(encoding="utf-8")
    assert 'href="style.css"' in text and 'src="notebook.js"' in text


def test_single_file_is_self_contained(tmp_path):
    text = b.build_single_file(tmp_path / "one.html").read_text(encoding="utf-8")
    assert "data:image/jpeg;base64," in text and "data:font/woff2;base64," in text
    assert 'href="style.css"' not in text and 'src="notebook.js"' not in text


def test_photo_and_name_open_the_index_page(page):
    index_page = page.split('data-token="about"')[0]
    assert index_page.index('class="photo"') < index_page.index("<h2>INDEX</h2>")
    assert page.count('class="photo"') == 1


def test_phone_is_on_the_index_page(page, profile):
    index_page = page.split('data-token="about"')[0]
    assert profile["phone"] in index_page
    assert 'href="tel:+19164775226"' in index_page


def test_cover_note_closes_the_notebook(page, profile):
    note = page.split('data-token="note"')[1]
    n = profile["cover_note"]
    assert b.esc(n["greeting"]) in note and b.esc(n["closing"]) in note
    for line in n["bring"]:
        assert b.esc(line) in note


def test_work_authorization_stamp_on_the_index_page(page, profile):
    index_page = page.split('data-token="about"')[0]
    w = profile["work_authorization"]
    assert f'<span class="stamp">{b.esc(w["status"])}</span>' in index_page
    assert b.esc(w["note"]) in index_page


def test_resume_pdf_download_on_the_index_page(page, profile):
    index_page = page.split('data-token="about"')[0]
    assert f'href="{profile["resume_pdf"]}" download' in index_page
    assert (b.ASSETS / profile["resume_pdf"]).read_bytes()[:5] == b"%PDF-"


def test_stamp_is_straight():
    css = (b.STATIC / "style.css").read_text(encoding="utf-8")
    stamp = css[css.index(".stamp{"):css.index("}", css.index(".stamp{"))]
    assert "rotate" not in stamp


def test_every_page_is_dated_by_the_script(page, pages):
    corners = re.findall(r'<span class="lbl">Date</span><span class="val js-date">([^<]*)</span>', page)
    assert len(corners) == len(pages)          # index included
    assert 'Date: <span class="js-date">' in page  # declaration
    js = (b.STATIC / "notebook.js").read_text(encoding="utf-8")
    assert "getDate() - 1" in js and ".js-date" in js


def test_spiral_binding_matches_the_ruling():
    css = (b.STATIC / "style.css").read_text(encoding="utf-8")
    rule = re.search(r"--u:(\d+)px", css).group(1)
    binding = css[css.index(".binding{"):css.index("}", css.index(".binding{"))]
    assert "data:image/svg+xml" in binding and f"/44px {rule}px repeat-y" in binding
