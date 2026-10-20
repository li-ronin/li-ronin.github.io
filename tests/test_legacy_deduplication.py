"""Guard the narrowly scoped 2023-and-earlier Blog duplicate cleanup."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent


class ArticleBody(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if not self.depth and dict(attrs).get('class') == 'article-content markdown-body':
            self.depth = 1
            return
        if self.depth:
            if tag == 'div':
                self.depth += 1
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.depth:
            if tag == 'div':
                self.depth -= 1
            if self.depth:
                self.parts.append('</' + tag + '>')

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


class LegacyDeduplicationTests(unittest.TestCase):
    def setUp(self):
        self.groups = json.loads((ROOT / 'data/legacy-deduplication.json').read_text())
        self.entries = json.loads((ROOT / 'data/writing.json').read_text())
        self.removed = {e['url'] for g in self.groups for e in g['remove']}

    def test_only_confirmed_old_blog_copies_are_removed(self):
        self.assertEqual(len(self.removed), 11)
        for group in self.groups:
            self.assertIn(group['keep'], self.entries)
            for entry in group['remove']:
                self.assertEqual(entry['kind'], 'blog')
                self.assertLess(entry['date'], '2024-01-01')
                self.assertNotIn(entry, self.entries)
                self.assertFalse((ROOT / entry['url'].lstrip('/')).exists())

    def test_canonical_body_html_is_preserved(self):
        for group in self.groups:
            source = (ROOT / group['keep']['url'].lstrip('/')).read_text()
            body = ''.join(ArticleBody(source).parts)
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), group['body_html_sha256'])

    def test_no_remaining_links_or_navigation_to_removed_posts(self):
        for path in ROOT.rglob('*.html'):
            for link in Links(path.read_text()).links:
                url = urlsplit(link.get('href', ''))
                if url.netloc and url.netloc != 'li-ronin.github.io':
                    continue
                target = unquote(url.path)
                self.assertNotIn(target, self.removed, str(path))
                if link.get('rel') in ('prev', 'next'):
                    self.assertNotEqual(target, '/' + str(path.relative_to(ROOT)))

    def test_retained_old_blog_bodies_are_not_identical(self):
        seen = set()
        for entry in self.entries:
            if entry['kind'] != 'blog' or entry['date'] >= '2024-01-01':
                continue
            body = ''.join(ArticleBody((ROOT / entry['url'].lstrip('/')).read_text()).parts)
            normalized = re.sub(r'\s+', '', body)
            self.assertNotIn(normalized, seen, entry['url'])
            seen.add(normalized)
        self.assertEqual(len(seen), 23)
