#!/usr/bin/env python3
"""Generate the interview archive. JSON is canonical; no network or dependencies."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'post/ai-interview-learning-archive.html'
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


def options(values):
    return '<option value="">全部</option>' + ''.join(f'<option value="{e(k)}">{e(v)}</option>' for k, v in values)


def render(data):
    questions = data['questions']
    sources = {s['id']: s for s in data['sources']}
    tags = Counter(t for q in questions for t in q['tags'])
    def source_link(sid):
        return f'<a href="#source-{e(sid)}">{e(sources[sid]["label"])}</a>'
    groups = []
    for category in CATEGORIES:
        cards = []
        selected = [q for q in questions if q['category'] == category]
        for q in sorted(selected, key=lambda q: (q['difficulty'], q['id'])):
            attrs = {'category': category, 'difficulty': str(q['difficulty']), 'roles': '|'.join(q['roles']), 'audience': '|'.join(q['audience']), 'tags': '|'.join(q['tags']), 'search': ' '.join([q['id'], q['title'], *q['tags'], *q['knowledge'], *q['extensions'], *q['followups']]).lower()}
            attr_string = ' '.join(f'data-{k}="{e(v)}"' for k, v in attrs.items())
            followups = '<h4>追问与辨析</h4>' + list_items(q['followups']) if q['followups'] else ''
            cards.append(f'''<article class="question" id="{e(q['id'])}" {attr_string}>
<div class="question-meta"><a href="#{e(q['id'])}" aria-label="题目永久链接 {e(q['id'])}">{e(q['id'])}</a><span>{LEVELS[q['difficulty']]}</span></div>
<h3>{e(q['title'])}</h3>
<div class="knowledge-tags" aria-label="知识标签">{''.join(f'<button type="button" class="knowledge-tag" disabled data-tag="{e(t)}" title="筛选知识：{e(t)}">{e(t)}</button>' for t in q['tags'])}</div>
<p class="question-scope">方向：{e(' / '.join(q['roles']))} · 适用学习：{e(' / '.join(q['audience']))} · 原面经招聘类别：{e(q['sourceAudience'])}</p>
<details><summary>知识点、延伸与追问</summary><div class="study-content"><h4>涉及知识</h4>{list_items(q['knowledge'])}<h4>延伸学习 / 动手验证</h4>{list_items(q['extensions'])}{followups}</div></details>
<p class="question-source">来源：{'；'.join(source_link(s) for s in q['sources'])}</p>
</article>''')
        if selected:
            groups.append(f'<section class="question-group" aria-label="{e(category)}"><h2>{e(category)} <span class="group-count">{len(selected)} 题</span></h2>' + '\n'.join(cards) + '</section>')
    source_items = []
    for s in data['sources']:
        link = f'<a href="{e(s["url"])}" rel="noreferrer">查看原文</a>' if s.get('url') else '本次提供的题目记录'
        details = ' · '.join(str(v) for v in [s.get('kind'), s.get('status'), ((s.get('dateType', '') + ' ' + s['date']) if s.get('date') else s.get('dateLabel'))] if v)
        source_items.append(f'<li id="source-{e(s["id"])}"><strong>{e(s["label"])}</strong> · {link}<br><span>{e(details)}<br>{e(s.get("note", ""))}</span></li>')
    resources = '<h3>导航页中的延伸资源</h3><ul>' + ''.join(f'<li><a href="{e(r["url"])}">{e(r["title"])}</a> · {e(r["status"])}</li>' for r in data.get('resources', [])) + '</ul>' if data.get('resources') else ''
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent 与大模型面试学习题库 · Khan Li</title>
<meta name="description" content="按知识领域与学习难度整理 Agent、RAG、大模型算法和工程面试题；保留来源，附知识点、延伸练习与追问，不提供标准答案。">
<link rel="canonical" href="https://li-ronin.github.io/post/ai-interview-learning-archive.html">
<link rel="icon" href="/images/alpaca.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/academic.css"><link rel="stylesheet" href="/assets/interviews.css">
<script src="/assets/interviews.js" defer></script></head><body><a class="skip-link" href="#main">跳到正文</a><div class="page interview-page">
<nav class="site-nav" aria-label="站点导航"><a class="site-name" href="/">李可涵 Khan Li</a><div class="site-nav-links"><a href="/">Home</a><a href="/blog/">Blog</a><a href="/notes/">Notes</a></div></nav>
<main id="main" tabindex="-1"><p class="eyebrow">LEARNING THROUGH QUESTIONS · 以问题组织学习</p><h1>Agent 与大模型<br>面试学习题库</h1>
<p class="page-description">不急着背答案。先看清一个问题连接哪些知识，再用实现、实验与项目证据建立理解。</p>
<div class="archive-stats"><span><strong>{len(questions)}</strong> 道归并题</span><span><strong>{len(groups)}</strong> 个知识领域</span><span><strong>{len(tags)}</strong> 个知识标签</span><span>更新于 <time datetime="{e(data['updated'])}">{e(data['updated'])}</time></span></div>
<section class="archive-guide" aria-label="使用说明"><p>收录范围：个人提供的题目记录与公开面经整理，不代表本站作者的面试经历。相近题合并，保留有区分度的追问；只列知识点与延伸，不展开答案。知识点、难度与延伸练习是本站的学习编排，不作为原面经提问的引文。</p><p>知识标签只表达具体知识，如「上下文压缩」「GraphRAG」「SFT」。难度是编者的学习分级，不是招聘方评级；校招 / 社招表示建议学习范围，与原面经招聘类别分开记录。</p><p>基础：解释概念与流程；进阶：实现方案和权衡；深入：跨模块约束、故障定位与验证。推荐顺序：概念基础 → 单链路实现 → 系统评测 → 项目表达。来源未明确的产品版本、招聘类别及缺失题干不作猜测。</p></section>
<form id="interview-filters" class="filters" role="search" hidden><div class="search-field"><label for="question-search">搜索题目、知识点或追问</label><input id="question-search" type="search" placeholder="例如：上下文压缩、GraphRAG、SFT" autocomplete="off"></div>
<div class="filter-grid"><label>知识领域<select id="category-filter">{options([(c,c) for c in CATEGORIES])}</select></label><label>知识标签<select id="tag-filter">{options([(t,f'{t} ({tags[t]})') for t in sorted(tags)])}</select></label><label>学习难度<select id="difficulty-filter">{options([(str(k),v) for k,v in LEVELS.items()])}</select></label><label>岗位方向<select id="role-filter">{options([(r,r) for r in sorted(set(r for q in questions for r in q['roles']))])}</select></label><label>适用学习<select id="audience-filter">{options([('校招','校招'),('社招','社招')])}</select></label></div>
<div class="filter-actions"><button type="reset">重置筛选</button><button type="button" id="expand-all">展开当前结果的学习线索</button><button type="button" id="collapse-all">收起学习线索</button><a href="#sources">来源与收录状态</a></div></form>
<noscript><p class="archive-guide">JavaScript 已关闭：全部题目仍可阅读，点击各题下方展开学习线索；筛选功能需要 JavaScript。</p></noscript>
<p id="result-count" class="result-count" aria-live="polite">共 {len(questions)} 道归并题，按领域与难度排列。</p><p id="no-results" hidden>没有匹配的题目。请减少筛选条件或尝试其他关键词。</p>
<div id="question-list">{''.join(groups)}</div>
<section id="sources" class="sources"><h2>来源与收录状态</h2><p>公开面经仅归纳问题主题，并非原文转载。原作者、原链接和读取限制保留于此；未读到正文的链接不用于生成题目。</p><ol>{''.join(source_items)}</ol>{resources}<p>本页内容由 <a href="/data/interviews.json">结构化题库数据</a> 生成，后续可逐题补充实验记录与答案。题号为稳定标识，新增题不改变已有题链接。</p></section>
</main><footer class="site-footer"><span>© 李可涵 Khan Li</span><a href="/blog/">返回 Blog</a></footer></div></body></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    html = render(load_data())
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != html:
            parser.exit(1, 'Interview page is out of date\n')
        print('Interview archive is current')
    else:
        OUTPUT.write_text(html, encoding='utf-8')
        print(OUTPUT)

if __name__ == '__main__':
    main()
