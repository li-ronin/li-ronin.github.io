import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('interviews', ROOT / 'scripts/build_interviews.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.anchors = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'): self.anchors.append(attrs['href'][1:])

class InterviewTests(unittest.TestCase):
    def setUp(self):
        self.data = builder.load_data()
        self.html = builder.render(self.data)
    def test_generated_page_is_current(self):
        self.assertEqual(builder.OUTPUT.read_text(), self.html)
    def test_all_questions_readable_without_javascript(self):
        for q in self.data['questions']:
            self.assertIn(builder.e(q['title']), self.html)
            self.assertIn('id="' + q['id'] + '"', self.html)
            for item in q['knowledge'] + q['extensions'] + q['followups']:
                self.assertIn(builder.e(item), self.html)
        self.assertNotIn('fetch(', (ROOT / 'assets/interviews.js').read_text())
    def test_no_duplicate_ids_and_all_anchors_resolve(self):
        parser = Parser()
        parser.feed(self.html)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertFalse(set(parser.anchors) - set(parser.ids))
    def test_tags_are_knowledge_not_level_or_recruitment(self):
        for q in self.data['questions']:
            self.assertTrue(set(q['tags']).isdisjoint({'校招','社招','基础','进阶','深入','Agent开发','大模型算法'}))
    def test_script_and_text_are_escaped(self):
        data = copy.deepcopy(self.data)
        data['questions'][0]['title'] = '<script>alert("x")</script>'
        html = builder.render(data)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert', html)
    def test_bad_source_urls_and_references_rejected(self):
        for mutate in [lambda d: d['sources'][0].update(url='javascript:alert(1)'), lambda d: d['questions'][0].update(sources=['unknown'])]:
            data = copy.deepcopy(self.data)
            mutate(data)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'data.json'
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError): builder.load_data(path)
    def test_blog_entry_points_to_archive(self):
        entries = json.loads((ROOT/'data/writing.json').read_text())
        found = [e for e in entries if e['url'] == '/post/ai-interview-learning-archive.html']
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['kind'], 'blog')
    def test_accessibility_and_progressive_enhancement(self):
        for token in ['lang="zh-CN"', 'name="viewport"', 'class="skip-link"', 'aria-live="polite"', '<noscript>', '<details>', '<summary>']:
            self.assertIn(token, self.html)
        self.assertEqual(self.html.count('<h1>'),1)
        self.assertIn('role="search" hidden', self.html)
    def test_user_question_coverage(self):
        coverage = self.data.get('coverage', [])
        self.assertTrue(coverage, 'Record source-question mapping to preserve supplied follow-ups')
        ids = {q['id'] for q in self.data['questions']}
        source_ids = {source['id'] for source in self.data['sources']}
        from collections import Counter
        counts = Counter()
        seen = set()
        for row in coverage:
            self.assertIn(row['sourceId'], source_ids)
            self.assertTrue(row['questionIds'])
            self.assertTrue(set(row['questionIds']).issubset(ids))
            key = (row['sourceId'], row['questionNumber'])
            self.assertNotIn(key, seen)
            seen.add(key)
            counts[row['sourceId']] += 1
        for sid, expected in {'user-notes':8, 'user-round1':22, 'user-round2':25, 'nowcoder-941992971027636224':24}.items():
            self.assertEqual(counts[sid], expected)
        for q in self.data['questions']:
            self.assertTrue(q['sources'])

if __name__ == '__main__': unittest.main()
