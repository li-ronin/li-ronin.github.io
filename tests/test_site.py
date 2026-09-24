"""Offline structural checks: python3 -m unittest discover -s tests -v."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_indexes", ROOT / "scripts/build_indexes.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.entries = builder.load_entries(ROOT / "data/writing.json")

    def test_homepage_is_profile_first(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="introduction"', home)
        self.assertNotIn('/post/', home)
        self.assertNotIn('<script', home)
        self.assertIn('href="/blog/"', home)
        self.assertIn('href="/notes/"', home)

    def test_generated_indexes_are_current(self):
        for kind, folder in (("blog", "blog"), ("note", "notes")):
            self.assertEqual((ROOT / folder / "index.html").read_text(encoding="utf-8"), builder.render_index(kind, self.entries))

    def test_every_entry_is_listed_once(self):
        blog = builder.render_index("blog", self.entries)
        notes = builder.render_index("note", self.entries)
        self.assertEqual(blog.count('class="entry"') + notes.count('class="entry"'), len(self.entries))
        self.assertNotIn('>摘录与感悟</a>', blog)
        self.assertIn('>摘录与感悟</a>', notes)

    def test_new_pages_have_accessibility_basics(self):
        for file in ('index.html', 'blog/index.html', 'notes/index.html'):
            text = (ROOT / file).read_text(encoding='utf-8')
            self.assertIn('lang="zh-CN"', text)
            self.assertIn('name="viewport"', text)
            self.assertIn('class="skip-link"', text)
            self.assertEqual(text.count('<h1'), 1)

    def test_html_in_titles_is_escaped(self):
        entry = {"date": "2026-09-24", "title": '<script>alert(1)</script>', "url": "/post/a&b.html", "kind": "blog"}
        text = builder.render_index('blog', [entry])
        self.assertNotIn('<script>', text)
        self.assertIn('&lt;script&gt;', text)
        self.assertIn('/post/a%26b.html', text)

    def assert_invalid(self, entries):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'writing.json'
            path.write_text(json.dumps(entries), encoding='utf-8')
            with self.assertRaises(ValueError):
                builder.load_entries(path)

    def test_external_urls_are_rejected(self):
        self.assert_invalid([dict(self.entries[0], url='https://example.com/a.html')])

    def test_duplicate_urls_are_rejected(self):
        self.assert_invalid([self.entries[0], self.entries[0]])

    def test_path_traversal_is_rejected(self):
        self.assert_invalid([dict(self.entries[0], url='/post/%2e%2e/a.html')])

    def test_invalid_dates_are_rejected(self):
        self.assert_invalid([dict(self.entries[0], date='2026-99-01')])

    def test_article_targets_exist(self):
        # Run this on the full checkout. Local preview bundles contain only changed files.
        if not (ROOT / 'post').is_dir():
            self.skipTest('Full legacy post directory is not present in this preview bundle')
        for entry in self.entries:
            self.assertTrue((ROOT / builder.unquote(entry['url']).lstrip('/')).is_file(), entry['url'])


if __name__ == '__main__':
    unittest.main()
