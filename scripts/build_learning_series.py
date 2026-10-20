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
SLUGS = ['agent-runtime', 'context-memory', 'tools-skills', 'planning-multi-agent',
         'llm-attention-inference', 'llm-training-alignment', 'rag-knowledge-engineering',
         'ai-coding-computer-use', 'agent-evaluation-reliability', 'concurrency-backpressure']
TITLE = 'Agent 与大模型：从原理到实现'
DATE = '2026-10-20'

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
            if key not in {'class','href','id','colspan','rowspan','scope'}: raise ValueError('Disallowed content attribute: ' + key)
            if key == 'href' and not (valid_url(value) or value.startswith('#')): raise ValueError('Unsafe content link')
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

def load_data(path=DATA):
    lessons = json.loads(Path(path).read_text(encoding='utf-8'))
    qdata = json.loads(QUESTIONS.read_text(encoding='utf-8'))
    qids = {q['id'] for q in qdata['questions']}
    if len(lessons) != 10 or {a['slug'] for a in lessons} != set(SLUGS): raise ValueError('Expected ten distinct lessons')
    seen_questions = set()
    for a in lessons:
        for key in ['title','category','summary']:
            if not isinstance(a.get(key),str) or not a[key].strip(): raise ValueError('Missing article '+key)
        if not a.get('sections') or not a.get('references'): raise ValueError('Article needs body and sources')
        if not isinstance(a.get('prerequisites'),list) or not all(isinstance(x,str) for x in a['prerequisites']): raise ValueError('Invalid prerequisites')
        if not isinstance(a.get('questionIds'),list) or not a['questionIds'] or not set(a['questionIds']) <= qids: raise ValueError('Unknown or missing question mapping in '+a['slug'])
        if len(a['questionIds'])!=len(set(a['questionIds'])): raise ValueError('Repeated article question mapping')
        seen_questions.update(a['questionIds'])
        seen_sections=set(); content_ids=[]; content_fragments=[]
        for s in a['sections']:
            if not re.fullmatch(r'[a-z][a-z0-9-]*',s['id']) or s['id'] in seen_sections: raise ValueError('Invalid/repeated section ID')
            seen_sections.add(s['id'])
            if not s.get('title') or not s.get('html'): raise ValueError('Empty section')
            validator=FragmentValidator();validator.feed(s['html']);validator.close()
            content_ids.extend(validator.ids);content_fragments.extend(validator.fragments)
        all_ids=['main','learning-questions','references',*seen_sections,*a['questionIds'],*content_ids]
        if len(all_ids)!=len(set(all_ids)): raise ValueError('Duplicate article DOM ID in '+a['slug'])
        if not set(content_fragments)<=set(all_ids): raise ValueError('Broken article fragment in '+a['slug'])
        for r in a['references']:
            if not r.get('title') or not valid_url(r.get('url','')): raise ValueError('Invalid technical reference')
        visible=' '.join([a['title'],a['summary'],*(s['title']+' '+plain(s['html']) for s in a['sections'])])
        if any(x in visible for x in ['面试题','题库','待补充']): raise ValueError('Unwanted question-bank framing')
    if seen_questions != qids: raise ValueError('Unmapped original questions: '+','.join(sorted(qids-seen_questions)))
    return sorted(lessons,key=lambda a:SLUGS.index(a['slug'])),qdata

def shell(title,description,path,body):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Khan Li</title><meta name="description" content="{e(description)}">
<link rel="canonical" href="https://li-ronin.github.io{e(path)}"><link rel="icon" href="/images/alpaca.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/academic.css"><link rel="stylesheet" href="/assets/learning-series.css"></head>
<body><a class="skip-link" href="#main">跳到正文</a><div class="page learning-series">
<nav class="site-nav" aria-label="站点导航"><a class="site-name" href="/">李可涵 Khan Li</a><div class="site-nav-links"><a href="/">Home</a><a href="/blog/">Blog</a><a href="/notes/">Notes</a></div></nav>
<main id="main" tabindex="-1">{body}</main><footer class="site-footer"><span>© 李可涵 Khan Li</span><a href="/blog/">返回 Blog</a></footer></div></body></html>'''

def render_hub(lessons,qdata):
    contents=[]
    for n,a in enumerate(lessons,1):
        contents.append(f'<li><h2><a href="{route(a["slug"])}">{n:02d} · {e(a["title"])}</a></h2><p>{e(a["summary"])}</p></li>')
    # Historical deep links stay meaningful without keeping all full questions on the hub.
    aliases=[]
    for q in qdata['questions']:
        a=next(a for a in lessons if q['id'] in a['questionIds'])
        aliases.append(f'<p class="legacy-target" id="{e(q["id"])}">此主题已移入 <a href="{route(a["slug"])}#{e(q["id"])}">{e(a["title"])}</a>。</p>')
    body=f'''<article><header class="article-header"><p class="series-label">系列导读</p><h1>{TITLE}</h1><p class="article-date"><time datetime="{DATE}">{DATE}</time></p>
<p>把零散的问题连成一条学习路线：先理解系统为什么这样设计，再走通一个具体例子，最后用代码与实验检验理解。</p>
<p>每个主题都是独立文章，包含原理、实现示例、失败场景与练习。可以按顺序阅读，也可以从正在遇到的问题进入。</p></header>
<section class="study-route"><h2>怎样阅读</h2><p>工程主线：运行时 → 上下文与记忆 → 工具 → 编排 → 开发工作流 → 评测与可靠性。模型主线：注意力与推理 → 训练与对齐 → RAG。并发一篇为两条主线提供系统基础。</p><p>先不用背结论。读完一节后，尝试画出数据流、手算示例或修改示例参数，再对照练习中的验证条件。涉及个人项目的问题，需要自己的日志与实验作答，文章不会替代真实证据。</p></section>
<ol class="series-list">{''.join(contents)}</ol>{''.join(aliases)}</article>'''
    return shell(TITLE,'十篇独立学习文章：Agent、上下文、工具、编排、LLM、RAG、开发工作流与系统工程。',HUB,body)

def render_article(a,lessons,qdata):
    index=SLUGS.index(a['slug'])
    questions={q['id']:q for q in qdata['questions']}
    sources={s['id']:s for s in qdata['sources']}
    toc=''.join(f'<li><a href="#{e(s["id"])}">{e(s["title"])}</a></li>' for s in a['sections'])
    chapters=''.join(f'<section class="lesson-section" id="{e(s["id"])}"><h2>{e(s["title"])}</h2>{s["html"]}</section>' for s in a['sections'])
    related=[]
    for qid in a['questionIds']:
        q=questions[qid]
        refs=[]
        for sid in q['sources']:
            s=sources[sid]
            if s.get('url'):
                refs.append(f'<a href="{e(s["url"])}">{e(s.get("author","原作者"))}</a>')
        origin=' · 资料线索：'+'、'.join(refs) if refs else ''
        practice = '【结合自己的项目证据】' if qid.startswith(('project-', 'career-')) or qid in {'harness-003','llm-004','llm-006','cost-001','eval-001','coding-001','coding-003','coding-004'} else ''
        if qid == 'harness-001': practice = '【先确认项目指代与版本】'
        related.append(f'<li id="{e(qid)}">{e(practice)}{e(q["title"])}<span class="question-origin">{origin}</span></li>')
    refs=''.join(f'<li><a href="{e(r["url"])}">{e(r["title"])}</a></li>' for r in a['references'])
    prev=f'<a rel="prev" href="{route(lessons[index-1]["slug"])}">上一篇：{e(lessons[index-1]["title"])}</a>' if index else '<span></span>'
    nxt=f'<a rel="next" href="{route(lessons[index+1]["slug"])}">下一篇：{e(lessons[index+1]["title"])}</a>' if index+1<len(lessons) else '<span></span>'
    tags=list(dict.fromkeys(t for qid in a['questionIds'] for t in questions[qid]['tags']))[:10]
    prerequisites='；'.join(a['prerequisites'])
    body=f'''<article class="blog-article"><p class="breadcrumb"><a href="{HUB}">{TITLE}</a> / {index+1:02d}</p>
<header class="article-header"><h1>{e(a['title'])}</h1><p class="article-date"><time datetime="{DATE}">{DATE}</time> · 技术资料核对日期；具体产品行为以对应版本为准</p><p>{e(a['summary'])}</p><p class="knowledge-tags">知识标签：{e(' · '.join(tags))}</p><p><strong>阅读前准备</strong>：{e(prerequisites)}</p></header>
<nav class="article-contents" aria-label="文章目录"><h2>目录</h2><ol>{toc}<li><a href="#learning-questions">带着这些问题回看</a></li><li><a href="#references">参考资料</a></li></ol></nav>
{chapters}<section id="learning-questions" class="learning-questions"><h2>带着这些问题回看</h2><p>下面保留最初的学习问题，用来检查理解是否能迁移到自己的任务。项目经历与实测指标需由真实工作补足，不代表本文已经给出个人经历的答案。</p><ul>{''.join(related)}</ul></section>
<section id="references" class="references"><h2>参考资料</h2><p>机制说明以原始论文、官方文档为依据；文中自建示例与设计建议不等同于任何产品的内部实现。</p><ol>{refs}</ol></section>
<nav class="article-pagination" aria-label="系列上一篇和下一篇">{prev}{nxt}</nav><p class="back-to-series"><a href="{HUB}">返回系列目录</a></p></article>'''
    return shell(a['title'],a['summary'],route(a['slug']),body)

def outputs(lessons,qdata):
    hub=render_hub(lessons,qdata)
    result={HUB:hub,LEGACY:hub}
    result.update({route(a['slug']):render_article(a,lessons,qdata) for a in lessons})
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    lessons,qdata=load_data()
    for url,html in outputs(lessons,qdata).items():
        p=ROOT/url.lstrip('/')
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8')!=html:parser.exit(1,'Out of date: '+str(p)+'\n')
        else:p.write_text(html,encoding='utf-8')
    print(('Checked' if args.check else 'Built')+' ten lessons and two series entry addresses')
if __name__=='__main__':main()
