"""Regression checks for shared article styling without rewriting legacy posts."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
NAME = '李可涵 Khan Li'


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ReadingTests(unittest.TestCase):
    def test_legacy_style_entry_uses_only_academic_styles(self):
        css = (ROOT / 'css/style.css').read_text(encoding='utf-8')
        self.assertEqual(css.count('@import'), 2)
        for filename in ('academic.css', 'reading.css'):
            self.assertIn('/assets/' + filename, css)
            self.assertTrue((ROOT / 'assets' / filename).is_file())
        self.assertNotIn('--home-banner-img', css)

    def test_homepage_full_name_and_approved_photo(self):
        home = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('李可涵 <span class="name-en">Khan Li</span>', home)
        self.assertIn('<title>' + NAME + '</title>', home)
        images = [attrs for tag, attrs in Elements(home).tags if tag == 'img']
        portrait = next(attrs for attrs in images if attrs.get('class') == 'portrait')
        self.assertEqual(portrait['src'], '/images/profile.jpg')
        self.assertEqual((portrait['width'], portrait['height']), ('220', '220'))

    def test_writing_indexes_use_full_name(self):
        for file in ('blog/index.html', 'notes/index.html'):
            with self.subTest(file=file):
                text = (ROOT / file).read_text(encoding='utf-8')
                self.assertIn('class="site-name" href="/">' + NAME, text)
                self.assertNotIn('李可涵 · LKH', text)

    def test_every_existing_article_uses_shared_entry_points(self):
        posts = list((ROOT / 'post').glob('*.html'))
        self.assertTrue(posts, 'Run these tests on a complete repository checkout')
        for file in posts:
            with self.subTest(file=file.name):
                tags = Elements(file.read_text(encoding='utf-8')).tags
                self.assertTrue(any(tag == 'link' and a.get('href') == '/css/style.css' for tag, a in tags))
                self.assertTrue(any(tag == 'script' and a.get('src') == '/js/main.js' for tag, a in tags))
                self.assertTrue(any('article-content' in a.get('class', '').split() and 'markdown-body' in a.get('class', '').split() for tag, a in tags))

    def test_enhancements_preserve_native_content_and_links(self):
        js = (ROOT / 'js/main.js').read_text(encoding='utf-8')
        self.assertIn('swup.destroy()', js)
        self.assertIn("getAttribute('data-src')", js)
        self.assertIn("querySelector('td.code pre')", js)
        self.assertIn('navigator.clipboard.writeText', js)
        self.assertNotIn('.innerHTML', js)
        self.assertNotIn('localStorage', js)

    def test_reading_styles_preserve_mobile_code_scrolling(self):
        css = (ROOT / 'assets/reading.css').read_text(encoding='utf-8')
        self.assertIn('overflow-x: auto', css)
        self.assertIn('white-space: pre;', css)
        self.assertIn('line-height: 1.65', css)
        self.assertIn('@media (max-width: 620px)', css)


if __name__ == '__main__':
    unittest.main()
