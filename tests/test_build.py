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


def test_experience_is_latest_first(page, profile):
    titles = re.findall(r'<div class="job-top"><b>(.*?)</b><span class="when">(.*?)</span>', page)
    assert titles[0] == ("Senior Software Engineer", "Mar 2022 – Jul 2026")
    assert titles[-1][1] == "Jan 2012 – Aug 2013"
    starts = [r["from"] for r in b.prepare_roles(profile["roles"])]
    assert starts == sorted(starts, reverse=True)
    assert len(titles) == len(profile["roles"])


def test_sections_in_classic_order(page):
    heads = re.findall(r'<span class="no">\d\.</span>(.*?) :-</h2>', page)
    assert heads == ["Career Objective", "Professional Summary", "Work Experience", "Projects",
                     "Technical Skills", "Educational Qualifications", "Certifications &amp; Awards", "Declaration"]


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
    assert "<script" not in page  # plain document, no JavaScript needed


def test_build_writes_site(tmp_path):
    index = b.build(tmp_path)
    for name in ["index.html", "style.css", "headshot.jpg", ".nojekyll"]:
        assert (tmp_path / name).exists(), name
    assert 'href="style.css"' in index.read_text(encoding="utf-8")


def test_single_file_is_self_contained(tmp_path):
    text = b.build_single_file(tmp_path / "one.html").read_text(encoding="utf-8")
    assert "data:image/jpeg;base64," in text
    assert 'href="style.css"' not in text
