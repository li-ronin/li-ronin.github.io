"""Question-first blog: verbatim occurrences, optional personal answers and safe static output."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('series',ROOT/'scripts/build_learning_series.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.tags=[];self.text=[];self.headings=[];self.current=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append(tag)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='h2':self.current=[a.get('id'),'']
    def handle_data(self,x):
        self.text.append(x)
        if self.current is not None:self.current[1]+=x
    def handle_endtag(self,tag):
        if tag=='h2' and self.current is not None:self.headings.append(self.current);self.current=None
class LearningSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lessons,cls.qdata=builder.load_data();cls.pages=builder.outputs(cls.lessons,cls.qdata)
    def test_thirteen_separate_articles(self):
        self.assertEqual(len(self.lessons),13);self.assertEqual(len(self.pages),15)
        hub=self.pages[builder.HUB];self.assertNotIn('class="question-answer"',hub)
        for a in self.lessons:self.assertIn(builder.route(a['slug']),hub)
    def test_versioned_series_stylesheet(self):
        for html in self.pages.values():
            self.assertIn('href="/assets/learning-series.css?v=20261024-answer-areas"',html)
    def test_generated_pages_current(self):
        for url,html in self.pages.items():self.assertEqual((ROOT/url.lstrip('/')).read_text(),html)
    def test_original_wording_is_heading_not_end_checklist(self):
        headings={}
        for a in self.lessons:
            html=self.pages[builder.route(a['slug'])];p=Parser();p.feed(html);headings.update(dict(p.headings))
            self.assertNotIn('带着这些问题回看',html)
            self.assertIn('class="question-answer writing-area is-empty"',html)
        self.assertEqual(len(self.qdata['originals']),79)
        for o in self.qdata['originals']:self.assertEqual(headings[o['id']],o['title'])
    def test_original_transcription_fingerprint(self):
        originals=self.qdata['originals']
        payload=json.dumps([(o['id'],o['title'],o['sourceId'],o['sourceRefNumber']) for o in originals],ensure_ascii=False,separators=(',',':'))
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), '9e4d2f060308219882f631dcd55cfe659b6ff208162193113b5f0b73ba1f4333')
        self.assertEqual(len({o['canonicalId'] for o in originals}),59)
    def test_all_concepts_have_authoring_slots(self):
        qids={q['id'] for q in self.qdata['questions']}
        self.assertEqual(set(self.qdata['answers']),qids);self.assertEqual(len(qids),89)
        for a in self.lessons:
            html=self.pages[builder.route(a['slug'])]
            for qid in a['questionIds']:
                self.assertIn('id="'+qid+'"',html)
                self.assertIn(self.qdata['answers'][qid]['renderedHtml'],html)
    def test_empty_fields_and_legacy_answers(self):
        for ans in self.qdata['answers'].values():
            self.assertEqual(ans['answerMarkdown'],'')
            self.assertEqual(ans['learningNotesMarkdown'],'')
            self.assertEqual(ans['sources'],[])
        for q in self.qdata['questions']:
            self.assertEqual(q['answer'],'')
            self.assertFalse(q.get('answerSources'))
        for html in self.pages.values():
            for unwanted in ['class="answer-references"','class="references"','项目经历与技术选择','阅读解答']:
                self.assertNotIn(unwanted,html)
        self.assertEqual(sum(html.count('原题中的项目来自所收集的记录，不代表本站作者经历。') for html in self.pages.values()),1)
    def test_future_personal_answer_and_notes_render_independently(self):
        data=json.loads(builder.ANSWERS.read_text())
        qid=data['questions'][0]['id']
        for answer,notes in [('我的理解。',''),('','实际学习记录。'),('短答案。','复现过程。')]:
            with self.subTest(answer=answer,notes=notes), tempfile.TemporaryDirectory() as tmp:
                data['questions'][0]['answerMarkdown']=answer
                data['questions'][0]['learningNotesMarkdown']=notes
                p=Path(tmp)/'answers.json';p.write_text(json.dumps(data))
                lessons,qdata=builder.load_data(answer_path=p)
                lesson=next(a for a in lessons if qid in a['questionIds'])
                html=builder.render_article(lesson,lessons,qdata)
                self.assertIn(builder.writing_area('question-answer','我的回答',qdata['answers'][qid]['renderedHtml']),html)
                self.assertIn(builder.writing_area('learning-notes','学习记录',qdata['answers'][qid]['renderedNotesHtml']),html)
                if answer:self.assertIn(answer,html)
                if notes:self.assertIn(notes,html)
    def test_empty_areas_are_visible_labeled_and_not_fake_inputs(self):
        for a in self.lessons:
            html=self.pages[builder.route(a['slug'])]
            count=len(a['questionIds'])
            self.assertEqual(html.count('class="question-answer writing-area is-empty"'),count)
            self.assertEqual(html.count('class="learning-notes writing-area is-empty"'),count)
            self.assertEqual(html.count('<h3 class="writing-area-title">我的回答</h3>'),count)
            self.assertEqual(html.count('<h3 class="writing-area-title">学习记录</h3>'),count)
            self.assertEqual(html.count('<div class="writing-area-body"></div>'),2*count)
    def test_whitespace_only_content_keeps_empty_regions(self):
        data=json.loads(builder.ANSWERS.read_text())
        for entry in data['questions']:
            entry['answerMarkdown']=' \n '
            entry['learningNotesMarkdown']='\t '
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'answers.json';p.write_text(json.dumps(data))
            lessons,qdata=builder.load_data(answer_path=p)
            self.assertEqual(builder.outputs(lessons,qdata),self.pages)
    def test_filled_regions_keep_long_prose_code_and_tables(self):
        text=('较长的学习理解。'*100)+'\n\n### 复现步骤\n\n```python\nprint("example")\n```\n\n| 项目 | 观察 |\n| --- | --- |\n| A | B |'
        rendered=builder.render_markdown(text)
        for kind,title in [('question-answer','我的回答'),('learning-notes','学习记录')]:
            html=builder.writing_area(kind,title,rendered)
            self.assertIn('writing-area has-content',html)
            self.assertIn(rendered,html)
            self.assertIn('<table>',html)
            self.assertIn('<pre>',html)
            self.assertNotIn('is-empty',html)
    def test_optional_markdown_type_validation(self):
        for field in ['answerMarkdown','learningNotesMarkdown']:
            data=json.loads(builder.ANSWERS.read_text());data['questions'][0][field]=None
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'answers.json';p.write_text(json.dumps(data))
                with self.assertRaises(ValueError):builder.load_data(answer_path=p)
    def test_original_tags_are_displayed_by_question(self):
        for lesson in self.lessons:
            html=self.pages[builder.route(lesson['slug'])]
            for qid in lesson['questionIds']:
                for o in builder.original_questions(qid,self.qdata):
                    self.assertIn('<h2 id="'+o['id']+'">'+builder.e(o['title'])+'</h2>'+builder.knowledge_tags(o['tags']),html)
    def test_external_questions_distinct(self):
        for a in self.lessons:
            if any(not builder.original_questions(qid,self.qdata) for qid in a['questionIds']):self.assertIn('延伸问题',self.pages[builder.route(a['slug'])])
    def test_safe_static_html(self):
        for url,html in self.pages.items():
            p=Parser();p.feed(html)
            self.assertTrue(set(p.tags).isdisjoint({'script','form','input','textarea','select','button','details','iframe'}))
            for bad in ['待补充','面试题库','搜索题目','Sentinel_','contenteditable','placeholder=']:self.assertNotIn(bad,html)
            self.assertEqual(p.tags.count('h1'),1);self.assertIn('name="viewport"',html)
    def test_internal_links_and_fragment_ids(self):
        parsed={}
        for url,html in self.pages.items():
            p=Parser();p.feed(html);parsed[url]=p;self.assertEqual(len(p.ids),len(set(p.ids)),url)
        for url,p in parsed.items():
            for href in p.links:
                u=urlsplit(href)
                if u.scheme or u.netloc:continue
                target=u.path or url
                if target in parsed and u.fragment:self.assertIn(u.fragment,parsed[target].ids,(url,href))
                elif u.path and u.path.endswith('.html'):self.assertTrue((ROOT/u.path.lstrip('/')).exists(),href)
    def test_source_references(self):
        for a in self.lessons:
            html=self.pages[builder.route(a['slug'])]
            for qid in a['questionIds']:
                for r in self.qdata['answers'][qid]['sources']:self.assertIn(builder.e(r['url']),html)
                originals=builder.original_questions(qid,self.qdata)
                source_ids=[o['sourceId'] for o in originals] if originals else next(q for q in self.qdata['questions'] if q['id']==qid)['sources']
                for sid in source_ids:
                    s=next(s for s in self.qdata['sources'] if s['id']==sid)
                    if s.get('url'):self.assertIn(builder.e(s['url']),html)
    def test_original_question_not_attributed_to_similar_external_concept(self):
        self.assertEqual(builder.source_links('tools-001',self.qdata),'')
        self.assertNotIn('zhuanlan.zhihu.com',builder.source_links('tools-001',self.qdata))
        self.assertIn('nowcoder.com',builder.source_links('computer-001',self.qdata))
    def test_all_articles_in_blog(self):
        entries=json.loads((ROOT/'data/writing.json').read_text())
        for a in self.lessons:
            url=builder.route(a['slug']);self.assertEqual(sum(e['url']==url for e in entries),1);self.assertIn(url,(ROOT/'blog/index.html').read_text())
    def test_no_private_identifiers_in_corpus(self):
        text=builder.ORIGINALS.read_text()
        for bad in ['Sentinel_','originalMessageId','latestCorrectionMessageId','room_id']:self.assertNotIn(bad,text)
    def test_fragment_validation_rejects_active_content(self):
        for html in ['<script>alert(1)</script>','<p onclick="x()">x</p>','<a href="javascript:x()">x</a>']:
            with self.assertRaises(ValueError):builder.FragmentValidator().feed(html)
    def test_load_rejects_bad_mapping(self):
        data=copy.deepcopy(self.lessons);data[0]['questionIds'].append('made-up')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json';p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):builder.load_data(p)
    def test_headings_escaped(self):
        a=copy.deepcopy(self.lessons[0]);a['title']='<script>bad</script>'
        html=builder.render_article(a,self.lessons,self.qdata)
        self.assertIn('&lt;script&gt;bad&lt;/script&gt;',html);self.assertNotIn('<script>bad',html)
    def test_responsive_and_legacy_links(self):
        css=(ROOT/'assets/learning-series.css').read_text()
        for term in ['overflow-x: auto','white-space: pre','@media (max-width: 620px)']:self.assertIn(term,css)
        self.assertEqual(self.pages[builder.HUB],self.pages[builder.LEGACY])
        for q in self.qdata['questions']:self.assertIn('id="'+q['id']+'"',self.pages[builder.LEGACY])
class MarkdownTests(unittest.TestCase):
    def test_escape_raw_html(self):self.assertIn('&lt;script&gt;',builder.render_markdown('<script>bad</script>'))
    def test_code_remains_literal(self):self.assertIn('<code>a &lt; b && x</code>',builder.render_markdown('```\na < b && x\n```').replace('&amp;','&'))
    def test_inline_and_source(self):
        s=builder.render_markdown('**粗体** 与 `x < y` [资料](https://example.com/a)')
        self.assertIn('<strong>粗体</strong>',s);self.assertIn('&lt;',s);self.assertIn('href="https://example.com/a"',s)
    def test_broken_fence_rejected(self):
        with self.assertRaises(ValueError):builder.render_markdown('```\nbroken')
    def test_tables(self):
        s=builder.render_markdown('| A | B |\n| --- | --- |\n| 1 | 2 |')
        self.assertIn('<table>',s);self.assertIn('<td>2</td>',s)
if __name__=='__main__':unittest.main()
