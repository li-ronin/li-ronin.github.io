#!/usr/bin/env python3
"""Generate the ordinary learning-notes article. JSON is canonical; no network or dependencies."""
import argparse
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'post/agent-llm-learning-notes.html'
LEGACY_OUTPUT = ROOT / 'post/ai-interview-learning-archive.html'
LEVELS = {1: '基础 · 理解概念', 2: '进阶 · 实现与取舍', 3: '深入 · 系统与验证'}
CATEGORIES = ['Agent架构与Harness', '上下文与记忆', '工具与Skills', '规划与多Agent', 'RAG与知识工程', 'LLM原理与训练', '评测与工程化', 'AI Coding与Computer Use', '并发与系统基础', '项目表达与职业判断']


def load_data(path=None):
    data = json.loads((path or ROOT / 'data/interviews.json').read_text(encoding='utf-8'))
    sources = {s['id']: s for s in data['sources']}
    if len(sources) != len(data['sources']):
        raise ValueError('Duplicate source ID')
    for s in sources.values():
        if s.get('url') and (urlsplit(s['url']).scheme != 'https' or not urlsplit(s['url']).netloc):
            raise ValueError('Expected https source URL')
    seen = set()
    for q in data['questions']:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', q['id']) or q['id'] in seen:
            raise ValueError('Invalid or duplicate question ID')
        seen.add(q['id'])
        if q['category'] not in CATEGORIES or q['difficulty'] not in LEVELS:
            raise ValueError('Invalid category or difficulty')
        for field in ['title', 'sourceAudience']:
            if not isinstance(q.get(field), str) or not q[field].strip():
                raise ValueError('Missing ' + field)
        for field in ['tags', 'roles', 'audience', 'knowledge', 'extensions', 'followups', 'sources']:
            if not isinstance(q.get(field), list) or not all(isinstance(x, str) and x for x in q[field]):
                raise ValueError('Invalid ' + field)
        if not isinstance(q.get('answer', ''), str):
            raise ValueError('Answer must be plain text')
        answer_sources = q.get('answerSources', [])
        if not isinstance(answer_sources, list):
            raise ValueError('Invalid answer sources')
        for source in answer_sources:
            if not isinstance(source, dict) or not isinstance(source.get('title'), str) or not source['title'].strip():
                raise ValueError('Answer source needs a title')
            url = source.get('url', '')
            if not isinstance(url, str) or urlsplit(url).scheme != 'https' or not urlsplit(url).netloc:
                raise ValueError('Expected https answer source URL')
        if not q['sources'] or any(s not in sources for s in q['sources']):
            raise ValueError('Unknown question source')
        if not q['tags'] or not q['knowledge'] or not q['extensions']:
            raise ValueError('Missing study metadata')
        if any(t in ['校招', '社招', '基础', '进阶', '深入', '简单', '困难', 'Agent开发', '大模型算法'] for t in q['tags']):
            raise ValueError('Tags must be concrete knowledge, not audience, difficulty or role')
    return data


def e(value):
    return escape(str(value), quote=True)


def list_items(items):
    return '<ul>' + ''.join('<li>' + e(t) + '</li>' for t in items) + '</ul>'


def paragraphs(text):
    """Plain-text answers are escaped; blank lines separate paragraphs."""
    return ''.join('<p>' + e(part).replace('\n', '<br>') + '</p>'
                   for part in re.split(r'\n\s*\n', text.strip()) if part.strip())


def render(data):
    sources = {s['id']: s for s in data['sources']}
    source_numbers = {sid: i + 1 for i, sid in enumerate(sources)}
    groups = []
    contents = []
    for index, category in enumerate(CATEGORIES, 1):
        selected = [q for q in data['questions'] if q['category'] == category]
        if not selected:
            continue
        category_id = 'topic-' + str(index)
        contents.append(f'<li><a href="#{category_id}">{e(category)}</a></li>')
        questions = []
        for q in selected:
            answer = paragraphs(q.get('answer', ''))
            if answer:
                answer_refs = '；'.join(f'<a href="{e(ref["url"])}">{e(ref["title"])}</a>' for ref in q.get('answerSources', []))
                citations = '<p class="answer-sources">参考文档：' + answer_refs + '</p>' if answer_refs else ''
                answer = '<div class="answer"><h4>理解与说明</h4>' + answer + citations + '</div>'
            further = ('<p><strong>继续思考</strong></p>' + list_items(q['followups'])) if q['followups'] else ''
            references = '、'.join(f'<a href="#source-{e(sid)}">[{source_numbers[sid]}]</a>' for sid in q['sources'])
            questions.append(f'''<section class="learning-question" id="{e(q['id'])}">
<h3><a class="question-heading" href="#{e(q['id'])}">{e(q['title'])}</a></h3>
<p class="knowledge-tags">知识标签：{e(' · '.join(q['tags']))}</p>
{answer}
<p><strong>涉及知识</strong>：{e('；'.join(q['knowledge']))}。</p>
<p><strong>延伸学习</strong></p>{list_items(q['extensions'])}
{further}<p class="question-reference">参考：{references}</p>
</section>''')
        groups.append(f'<section class="learning-topic" id="{category_id}"><h2>{e(category)}</h2>' + '\n'.join(questions) + '</section>')
    source_items = []
    for index, s in enumerate(data['sources'], 1):
        if s.get('url'):
            platform = '知乎' if 'zhihu.com' in s['url'] else '牛客网'
            label = f'{s.get("author", "原作者")} · {platform}'
            link = f'<a href="{e(s["url"])}" rel="noreferrer">{e(label)}</a>'
            detail = '仅参考公开可见部分。' if s.get('status') == '仅读取免费预览' else '问题主题经归纳整理，原文内容请见链接。'
            if s.get('kind') == '资源导航':
                detail = '资源导航，列于延伸阅读；未据此补写内容。'
        else:
            link = '学习问题记录 ' + str(index)
            detail = '整理时保留的问题与思考线索。'
        source_items.append(f'<li id="source-{e(s["id"])}">{link}<span class="reference-note"> · {e(detail)}</span></li>')
    resources = ''
    if data.get('resources'):
        resources = '<h3>延伸阅读</h3><ul>' + ''.join(
            f'<li><a href="{e(r["url"])}">资料链接 {i}</a>（来自资源导航，正文尚未核对）</li>'
            for i, r in enumerate(data['resources'], 1)) + '</ul>'
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent 与大模型学习笔记 · Khan Li</title>
<meta name="description" content="围绕 Agent、上下文与记忆、RAG、大模型训练及工程实践，按知识主题记录问题、答案与延伸思考。">
<link rel="canonical" href="https://li-ronin.github.io/post/agent-llm-learning-notes.html">
<link rel="icon" href="/images/alpaca.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/academic.css"><link rel="stylesheet" href="/assets/learning-notes.css">
</head><body><a class="skip-link" href="#main">跳到正文</a><div class="page learning-notes">
<nav class="site-nav" aria-label="站点导航"><a class="site-name" href="/">李可涵 Khan Li</a><div class="site-nav-links"><a href="/">Home</a><a href="/blog/">Blog</a><a href="/notes/">Notes</a></div></nav>
<main id="main" tabindex="-1"><article class="blog-article">
<header class="article-header"><h1>Agent 与大模型学习笔记</h1><p class="article-date"><time datetime="{e(data['updated'])}">{e(data['updated'])}</time></p>
<p>以问题为起点，逐步整理 Agent、大模型与工程实践中的知识。在可核对的基础知识后记录理解与说明；需要结合具体项目、版本或实践验证的问题，保留知识点和延伸思考。</p><p class="article-date">技术资料核对于 2026 年 10 月 20 日；具体产品行为以对应版本为准。</p></header>
<nav class="article-contents" aria-label="文章目录"><h2>目录</h2><ol>{''.join(contents)}<li><a href="#references">参考资料</a></li></ol></nav>
{''.join(groups)}
<section id="references" class="references"><h2>参考资料</h2><p>外部资料仅提炼问题主题，保留原作者与原文链接。以下学习线索不等同于原文答案。</p><ol>{''.join(source_items)}</ol>{resources}</section>
</article></main><footer class="site-footer"><span>© 李可涵 Khan Li</span><a href="/blog/">返回 Blog</a></footer></div></body></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    html = render(load_data())
    # Keep the historical address and all question anchors readable without JS.
    for output in (OUTPUT, LEGACY_OUTPUT):
        if args.check:
            if not output.exists() or output.read_text(encoding='utf-8') != html:
                parser.exit(1, 'Learning notes are out of date: ' + str(output) + '\n')
        else:
            output.write_text(html, encoding='utf-8')
            print(output)
    if args.check:
        print('Learning notes and historical URL are current')


if __name__ == '__main__':
    main()
