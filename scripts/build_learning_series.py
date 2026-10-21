#!/usr/bin/env python3
"""Render a script-free, multi-article learning series from reviewed HTML fragments."""
import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/learning-series.json'
QUESTIONS = ROOT / 'data/interviews.json'
HUB = '/post/agent-llm-learning-notes.html'
LEGACY = '/post/ai-interview-learning-archive.html'
SLUGS = ['agent-runtime', 'context-memory', 'agent-memory', 'tools-skills', 'planning-multi-agent',
         'llm-attention-inference', 'llm-training-alignment', 'rag-data-updates', 'rag-knowledge-engineering',
         'ai-coding-computer-use', 'agent-evaluation-reliability', 'concurrency-backpressure', 'project-experience']
TITLE = 'Agent 与大模型：问题与解答'
DATE = '2026-10-21'
ORIGINALS = ROOT / 'data/original-questions.json'
ANSWERS = ROOT / 'data/question-answers.json'
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
from markdown_subset import render as render_markdown

def e(value): return escape(str(value), quote=True)
def route(slug): return '/post/learning-' + slug + '.html'
def valid_url(url):
    p = urlsplit(url)
    return p.scheme == 'https' and bool(p.netloc) and not p.username and not p.password

class FragmentValidator(HTMLParser):
    allowed = {'p','ul','ol','li','pre','code','table','thead','tbody','tr','th','td','caption',
               'strong','em','b','i','br','hr','a','h3','h4','h5','blockquote','sup','sub','span','div','dl','dt','dd'}
    def __init__(self): super().__init__(); self.stack=[]; self.ids=[]; self.fragments=[]
    def handle_starttag(self, tag, attrs):
        if tag not in {'br','hr'}: self.stack.append(tag)
        if tag not in self.allowed: raise ValueError('Disallowed content tag: ' + tag)
        for key, value in attrs:
            if key not in {'class','href','id','colspan','rowspan','scope','start'}: raise ValueError('Disallowed content attribute: ' + key)
            if key == 'href' and not (valid_url(value) or value.startswith('#')): raise ValueError('Unsafe content link')
            if key == 'start' and (tag != 'ol' or not value.isdigit()): raise ValueError('Invalid list start')
            if key == 'id':
                if not re.fullmatch(r'[a-z][a-z0-9-]*', value): raise ValueError('Invalid fragment ID')
                self.ids.append(value)
            if key == 'href' and value.startswith('#'): self.fragments.append(value[1:])
    def handle_endtag(self, tag):
        if tag in {'br','hr'}: return
        if not self.stack or self.stack.pop()!=tag: raise ValueError('Unbalanced content HTML: '+tag)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in {'br','hr'}: self.handle_endtag(tag)
    def close(self):
        super().close()
        if self.stack: raise ValueError('Unclosed content HTML: '+','.join(self.stack))

class PlainText(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self, data): self.parts.append(data)

def plain(html):
    p=PlainText(); p.feed(html); return ''.join(p.parts)

def shell(title,description,path,body):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Khan Li</title><meta name="description" content="{e(description)}">
<link rel="canonical" href="https://li-ronin.github.io{e(path)}"><link rel="icon" href="/images/alpaca.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/academic.css"><link rel="stylesheet" href="/assets/learning-series.css"></head>
<body><a class="skip-link" href="#main">跳到正文</a><div class="page learning-series">
<nav class="site-nav" aria-label="站点导航"><a class="site-name" href="/">李可涵 Khan Li</a><div class="site-nav-links"><a href="/">Home</a><a href="/blog/">Blog</a><a href="/notes/">Notes</a></div></nav>
<main id="main" tabindex="-1">{body}</main><footer class="site-footer"><span>© 李可涵 Khan Li</span><a href="/blog/">返回 Blog</a></footer></div></body></html>'''

def load_data(path=DATA, answer_path=ANSWERS, original_path=ORIGINALS):
    lessons=json.loads(Path(path).read_text(encoding='utf-8'))
    qdata=json.loads(QUESTIONS.read_text(encoding='utf-8'))
    corpus=json.loads(Path(original_path).read_text(encoding='utf-8'))
    answers=json.loads(Path(answer_path).read_text(encoding='utf-8'))
    answer_list=answers['questions'] if isinstance(answers,dict) else answers
    by_id={a['id']:a for a in answer_list}
    qids={q['id'] for q in qdata['questions']}
    if len(by_id)!=len(answer_list):raise ValueError('Duplicate answer IDs')
    if set(by_id)!=qids:raise ValueError('Missing or unknown answers: '+str(qids.symmetric_difference(by_id)))
    if [a['slug'] for a in lessons]!=SLUGS:raise ValueError('Unexpected article routes or order')
    mapped=[qid for a in lessons for qid in a['questionIds']]
    if len(mapped)!=len(set(mapped)) or set(mapped)!=qids:raise ValueError('Every concept must belong to exactly one article')
    originals=corpus['questions']
    if len(originals)!=79 or len({o['id'] for o in originals})!=79:raise ValueError('Original occurrence loss or duplicate')
    for o in originals:
        if not o['title'] or o['canonicalId'] not in qids:raise ValueError('Invalid original question')
    for a in lessons:
        if not a.get('title'):raise ValueError('Missing article title')
        ids={'main','references'};fragments=[]
        for qid in a['questionIds']:
            ans=by_id[qid]
            if not isinstance(ans.get('answerMarkdown'),str) or len(ans['answerMarkdown'].strip())<80:raise ValueError('Missing substantive answer: '+qid)
            html=render_markdown(ans['answerMarkdown']);v=FragmentValidator();v.feed(html);v.close()
            own=[qid,*[o['id'] for o in originals if o['canonicalId']==qid],*v.ids]
            if len(own)!=len(set(own)) or ids.intersection(own):raise ValueError('Duplicate DOM ID')
            ids.update(own);fragments.extend(v.fragments)
            ans['renderedHtml']=html
            if not isinstance(ans.get('sources'),list):raise ValueError('Answer sources must be list')
            for r in ans['sources']:
                if not r.get('title') or not valid_url(r.get('url','')):raise ValueError('Unsafe technical reference')
            for bad in ['待补充','面试题库']:
                if bad in ans['answerMarkdown']:raise ValueError('Unwanted placeholder or framing')
        if not set(fragments)<=ids:raise ValueError('Broken answer fragment')
    qdata['originals']=originals;qdata['answers']=by_id
    return lessons,qdata

def original_questions(qid,qdata):return [o for o in qdata['originals'] if o['canonicalId']==qid]
def question_label(qid,qdata):
    originals=original_questions(qid,qdata)
    return originals[0]['title'] if originals else next(q['title'] for q in qdata['questions'] if q['id']==qid)
def source_links(qid,qdata):
    q=next(q for q in qdata['questions'] if q['id']==qid);sources={s['id']:s for s in qdata['sources']}
    originals=original_questions(qid,qdata)
    # A similar externally collected concept is not the source of a verbatim user question.
    source_ids=list(dict.fromkeys(o['sourceId'] for o in originals)) if originals else q['sources']
    seen=set();out=[]
    for sid in source_ids:
        s=sources[sid];url=s.get('url')
        if url and url not in seen:
            seen.add(url);out.append('<a href="'+e(url)+'">'+e(s.get('author') or s.get('title') or '原文')+'</a>')
    return '、'.join(out)

def render_hub(lessons,qdata):
    cards=[]
    for a in lessons:
        own=[qid for qid in a['questionIds'] if original_questions(qid,qdata)]
        examples=''.join('<li><a href="'+route(a['slug'])+'#'+qid+'">'+e(question_label(qid,qdata))+'</a></li>' for qid in own[:3])
        cards.append('<li><h2><a href="'+route(a['slug'])+'">'+e(a['title'])+'</a></h2><ul class="question-preview">'+examples+'</ul></li>')
    aliases=[]
    for q in qdata['questions']:
        a=next(a for a in lessons if q['id'] in a['questionIds'])
        aliases.append('<p class="legacy-target" id="'+q['id']+'">'+e(question_label(q['id'],qdata))+'：<a href="'+route(a['slug'])+'#'+q['id']+'">阅读解答</a></p>')
    body='<article><header class="article-header"><h1>'+TITLE+'</h1><p class="article-date">更新于 '+DATE+'</p><p>按知识主题整理问题。打开一篇文章后，先看到原问题，再阅读对应的解释、例子与参考资料。相近问题放在一起，但保留不同的原始问法。</p><p>补充整理的问题单独标为“延伸问题”。涉及个人项目的内容说明如何分析和验证，不虚构项目经历或实测结果。</p></header><ol class="series-list">'+''.join(cards)+'</ol>'+''.join(aliases)+'</article>'
    return shell(TITLE,'保留原问题，逐题解释 Agent、上下文、工具、RAG、大模型和并发知识。',HUB,body)

def render_article(a,lessons,qdata):
    index=SLUGS.index(a['slug']);questions={q['id']:q for q in qdata['questions']}
    ordered=sorted(a['questionIds'],key=lambda qid:not bool(original_questions(qid,qdata)))
    toc=''.join('<li><a href="#'+(o['id'] if o else qid)+'">'+e(o['title'] if o else question_label(qid,qdata))+'</a></li>' for qid in ordered for o in (original_questions(qid,qdata) or [None]))
    parts=[];external_started=False;references=[];reference_urls=set()
    for qid in ordered:
        originals=original_questions(qid,qdata);ans=qdata['answers'][qid]
        if not originals and not external_started:
            parts.append('<div class="extension-intro"><h2>延伸问题</h2><p>以下是根据外部资料另外整理的问题，不是上面原记录的逐字转录。</p></div>');external_started=True
        headings=[]
        if originals:
            for n,o in enumerate(originals):
                if n:headings.append('<p class="variant-label">相关原问题：</p>')
                headings.append('<h2 id="'+o['id']+'">'+e(o['title'])+'</h2>')
                if o.get('editorNote'):headings.append('<p class="editor-note">'+e(o['editorNote'])+'</p>')
        else:headings.append('<h2>'+e(questions[qid]['title'])+'</h2>')
        origin=source_links(qid,qdata)
        origin_html='<p class="question-origin">问题来源：'+origin+'</p>' if origin else ''
        answer_refs=[]
        for r in ans['sources']:
            if r['url'] not in reference_urls:references.append(r);reference_urls.add(r['url'])
            answer_refs.append('<a href="'+e(r['url'])+'">'+e(r['title'])+'</a>')
        ref_html='<p class="answer-references">本题参考：'+'；'.join(answer_refs)+'</p>' if answer_refs else ''
        parts.append('<section class="lesson-section question-section" id="'+qid+'">'+''.join(headings)+origin_html+'<div class="question-answer">'+ans['renderedHtml']+'</div>'+ref_html+'</section>')
    refs=''.join('<li><a href="'+e(r['url'])+'">'+e(r['title'])+'</a></li>' for r in references)
    prev='<a rel="prev" href="'+route(lessons[index-1]['slug'])+'">上一篇：'+e(lessons[index-1]['title'])+'</a>' if index else '<span></span>'
    nxt='<a rel="next" href="'+route(lessons[index+1]['slug'])+'">下一篇：'+e(lessons[index+1]['title'])+'</a>' if index+1<len(lessons) else '<span></span>'
    tags=list(dict.fromkeys(t for qid in a['questionIds'] for t in questions[qid]['tags']))[:10]
    body='<article class="blog-article"><p class="breadcrumb"><a href="'+HUB+'">问题与解答</a> / '+e(a['title'])+'</p><header class="article-header"><h1>'+e(a['title'])+'</h1><p class="article-date">更新于 <time datetime="'+DATE+'">'+DATE+'</time></p><p class="knowledge-tags">知识标签：'+e(' · '.join(tags))+'</p></header><nav class="article-contents" aria-label="文章目录"><h2>本篇问题</h2><ol>'+toc+'</ol></nav>'+''.join(parts)+'<section id="references" class="references"><h2>参考资料</h2><p>产品实现可能随版本变化；示例中的假设与实测结论应当区分。</p><ol>'+refs+'</ol></section><nav class="article-pagination" aria-label="系列上一篇和下一篇">'+prev+nxt+'</nav><p class="back-to-series"><a href="'+HUB+'">返回问题目录</a></p></article>'
    return shell(a['title'],'围绕原问题解释'+a['title']+'，包含具体例子与参考资料。',route(a['slug']),body)

def outputs(lessons,qdata):
    hub=render_hub(lessons,qdata)
    return {HUB:hub,LEGACY:hub,**{route(a['slug']):render_article(a,lessons,qdata) for a in lessons}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    lessons,qdata=load_data()
    for url,html in outputs(lessons,qdata).items():
        p=ROOT/url.lstrip('/')
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8')!=html:parser.exit(1,'Out of date: '+str(p)+'\n')
        else:p.write_text(html,encoding='utf-8')
    print(('Checked' if args.check else 'Built')+' 13 question-first articles and two entry addresses')
if __name__=='__main__':main()
