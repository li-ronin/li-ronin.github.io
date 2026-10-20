"""Regression tests for the multi-article teaching series and original coverage."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('series', ROOT/'scripts/build_learning_series.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.tags=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append(tag)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and a.get('href'):self.links.append(a['href'])
    def handle_data(self,x):self.text.append(x)
class LearningSeriesTests(unittest.TestCase):
    def setUp(self):self.lessons,self.qdata=builder.load_data();self.pages=builder.outputs(self.lessons,self.qdata)
    def test_ten_distinct_articles_and_short_hub(self):
        self.assertEqual(len(self.lessons),10);self.assertEqual(len(self.pages),12)
        hub=self.pages[builder.HUB]
        self.assertNotIn('class="lesson-section"',hub)
        self.assertNotIn('理解与说明',hub)
        self.assertLess(len(builder.plain(hub)),6500)
        for a in self.lessons:self.assertIn(builder.route(a['slug']),hub)
    def test_generated_pages_current(self):
        for url,html in self.pages.items():self.assertEqual((ROOT/url.lstrip('/')).read_text(),html)
    def test_safe_static_html_and_no_question_bank_ui(self):
        for url,html in self.pages.items():
            with self.subTest(url=url):
                p=Parser();p.feed(html)
                self.assertTrue(set(p.tags).isdisjoint({'script','form','input','select','button','details','iframe'}))
                for bad in ['待补充','面试题','面经','校招','社招','搜索题目']:self.assertNotIn(bad,''.join(p.text))
                self.assertEqual(p.tags.count('h1'),1)
                self.assertIn('name="viewport"',html);self.assertIn('class="skip-link"',html)
    def test_internal_links_and_fragment_ids(self):
        parsed={}
        for url,html in self.pages.items():
            p=Parser();p.feed(html);parsed[url]=p
            self.assertEqual(len(p.ids),len(set(p.ids)),url)
        for url,p in parsed.items():
            for href in p.links:
                u=urlsplit(href)
                if u.scheme or u.netloc:continue
                target=u.path or url
                if target in parsed and u.fragment:self.assertIn(u.fragment,parsed[target].ids,(url,href))
                elif u.path and u.path.endswith('.html'):self.assertTrue((ROOT/u.path.lstrip('/')).exists(),href)
    def test_all_original_questions_mapped_and_rendered(self):
        qids={q['id'] for q in self.qdata['questions']};mapped=set()
        for a in self.lessons:
            mapped.update(a['questionIds']);html=self.pages[builder.route(a['slug'])]
            for qid in a['questionIds']:self.assertIn('id="'+qid+'"',html)
        self.assertEqual(len(qids),89);self.assertEqual(mapped,qids)
        from collections import Counter
        counts=Counter(r['sourceId'] for r in self.qdata['coverage'])
        for sid,n in {'user-notes':8,'user-round1':22,'user-round2':25,'nowcoder-941992971027636224':24}.items():self.assertEqual(counts[sid],n)
        for r in self.qdata['coverage']:self.assertTrue(set(r['questionIds'])<=qids)
    def test_source_references_and_original_authorship_preserved(self):
        for a in self.lessons:
            html=self.pages[builder.route(a['slug'])]
            for r in a['references']:self.assertIn(builder.e(r['url']),html)
            for qid in a['questionIds']:
                q=next(q for q in self.qdata['questions'] if q['id']==qid)
                for sid in q['sources']:
                    s=next(s for s in self.qdata['sources'] if s['id']==sid)
                    if s.get('url'):self.assertIn(builder.e(s['url']),html)
    def test_articles_have_substance_and_separate_navigation(self):
        for a in self.lessons:
            html=self.pages[builder.route(a['slug'])]
            self.assertGreaterEqual(len(a['sections']),5)
            self.assertGreater(len(builder.plain(''.join(s['html'] for s in a['sections']))),1800)
            self.assertIn('aria-label="文章目录"',html);self.assertIn('返回系列目录',html)
            self.assertIn('项目经历与实测指标需由真实工作补足',html)
    def test_all_articles_in_blog_index(self):
        entries=json.loads((ROOT/'data/writing.json').read_text())
        for url in [builder.HUB,*[builder.route(a['slug']) for a in self.lessons]]:
            self.assertEqual(sum(e['url']==url for e in entries),1)
            self.assertIn(url,(ROOT/'blog/index.html').read_text())
    def test_fragment_validation_rejects_active_content(self):
        for html in ['<script>alert(1)</script>','<p onclick="x()">x</p>','<a href="javascript:x()">x</a>','<img src=x onerror=x()>']:
            with self.assertRaises(ValueError):builder.FragmentValidator().feed(html)
    def test_load_rejects_bad_mapping_and_reference(self):
        for mutation in [lambda a:a[0].update(questionIds=['made-up']),lambda a:a[0]['references'][0].update(url='javascript:x()')]:
            data=copy.deepcopy(self.lessons);mutation(data)
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'lessons.json';p.write_text(json.dumps(data))
                with self.assertRaises(ValueError):builder.load_data(p)
    def test_load_rejects_dom_collisions_dead_fragments_and_unbalanced_html(self):
        for fragment in ['<p id="references">collision</p>', '<a href="#missing-target">dead link</a>', '<p><strong>broken</p>']:
            data=copy.deepcopy(self.lessons);data[0]['sections'][0]['html']+=fragment
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'lessons.json';p.write_text(json.dumps(data))
                with self.assertRaises(ValueError):builder.load_data(p)
    def test_headings_escaped(self):
        a=copy.deepcopy(self.lessons[0]);a['title']='<script>bad</script>'
        html=builder.render_article(a,self.lessons,self.qdata)
        self.assertIn('&lt;script&gt;bad&lt;/script&gt;',html);self.assertNotIn('<script>bad',html)
    def test_responsive_code_tables_and_legacy_hub(self):
        css=(ROOT/'assets/learning-series.css').read_text()
        for term in ['overflow-x: auto','white-space: pre','@media (max-width: 620px)']:self.assertIn(term,css)
        self.assertEqual(self.pages[builder.HUB],self.pages[builder.LEGACY])
        for q in self.qdata['questions']:self.assertIn('id="'+q['id']+'"',self.pages[builder.LEGACY])
if __name__=='__main__':unittest.main()
