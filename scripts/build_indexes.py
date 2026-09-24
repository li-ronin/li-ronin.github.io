#!/usr/bin/env python3
"""Build the static Blog/Notes indexes with Python's standard library only."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import sys
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent


def load_entries(path: Path) -> list[dict[str, str]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("writing.json must contain a list")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each entry must be an object")
        for key in ("date", "title", "url", "kind"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f"Missing or invalid field: {key}")
        date.fromisoformat(entry["date"])
        if len(entry["date"]) != 10:
            raise ValueError("Dates must use YYYY-MM-DD")
        if entry["kind"] not in {"blog", "note"}:
            raise ValueError("kind must be blog or note")
        url = urlsplit(entry["url"])
        path = unquote(url.path)
        if (url.scheme or url.netloc or url.query or url.fragment
                or not path.startswith("/post/") or not path.endswith(".html")
                or ".." in path.split("/") or "\\" in path
                or any(ord(char) < 32 for char in path)):
            raise ValueError(f"Expected a local /post/*.html URL: {entry['url']}")
        if path in seen:
            raise ValueError(f"Duplicate URL: {entry['url']}")
        seen.add(path)
    return sorted(entries, key=lambda entry: entry["date"], reverse=True)


def render_index(kind: str, entries: list[dict[str, str]]) -> str:
    is_blog = kind == "blog"
    label = "Blog" if is_blog else "Notes"
    chinese = "技术博客" if is_blog else "生活随笔"
    route = "/blog/" if is_blog else "/notes/"
    description = "学习笔记、问题分析与实践总结。" if is_blog else "阅读中的摘录，以及日常的观察与思考。"
    selected = [entry for entry in entries if entry["kind"] == kind]
    sections = []
    for year in dict.fromkeys(entry["date"][:4] for entry in selected):
        items = []
        for entry in selected:
            if entry["date"][:4] != year:
                continue
            href = escape(quote(unquote(entry["url"]), safe="/"), quote=True)
            items.append(f'        <li class="entry"><time datetime="{entry["date"]}">{entry["date"]}</time><a href="{href}">{escape(entry["title"])}</a></li>')
        sections.append(f'    <section class="year-group" aria-labelledby="year-{year}">\n      <h2 id="year-{year}">{year}</h2>\n      <ul class="entry-list">\n' + "\n".join(items) + '\n      </ul>\n    </section>')
    content = "\n".join(sections) if sections else '    <p class="empty">这里还没有文章。</p>'
    blog_current = ' aria-current="page"' if is_blog else ""
    notes_current = ' aria-current="page"' if not is_blog else ""
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="LKH 的{chinese}。{description}">
  <meta name="author" content="李可涵">
  <link rel="canonical" href="https://li-ronin.github.io{route}">
  <link rel="icon" href="/images/alpaca.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/academic.css">
  <title>{label} · {chinese} · LKH</title>
</head>
<body>
  <a class="skip-link" href="#main">跳到正文</a>
  <div class="page">
    <nav class="site-nav" aria-label="站点导航">
      <a class="site-name" href="/">李可涵 · LKH</a>
      <div class="site-nav-links"><a href="/">Home</a><a href="/blog/"{blog_current}>Blog</a><a href="/notes/"{notes_current}>Notes</a></div>
    </nav>
    <main id="main" tabindex="-1">
      <h1>{label} <span class="heading-translation">{chinese}</span></h1>
      <p class="page-description">{description} 共 {len(selected)} 篇。</p>
{content}
    </main>
    <footer class="site-footer"><span>© LKH</span><a href="/archives/">全部文章归档</a></footer>
  </div>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated files without modifying them")
    args = parser.parse_args()
    try:
        entries = load_entries(ROOT / "data/writing.json")
        stale = []
        for kind, folder in (("blog", "blog"), ("note", "notes")):
            path = ROOT / folder / "index.html"
            content = render_index(kind, entries)
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != content:
                    stale.append(str(path.relative_to(ROOT)))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        if stale:
            print("Out-of-date indexes: " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"{'Checked' if args.check else 'Built'} indexes for {len(entries)} entries.")
        return 0
    except (OSError, ValueError) as error:
        print(f"Index build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
