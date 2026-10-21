"""Small, escaped Markdown renderer for repository-owned teaching text.

Supported: paragraphs, headings, flat lists, fenced code, tables, inline links,
strong/emphasis and code. Raw HTML is text; no extensions or external runtime.
"""
import re
from html import escape
from urllib.parse import urlsplit

def inline(text):
    tokens=[]
    def token(value):
        tokens.append(value);return '\x00'+str(len(tokens)-1)+'\x00'
    text=re.sub(r'`([^`\n]+)`',lambda m:token('<code>'+escape(m[1])+'</code>'),text)
    def link(m):
        url=m[2];p=urlsplit(url)
        if p.scheme!='https' or not p.netloc or p.username or p.password:
            return m[0]
        return token('<a href="'+escape(url,quote=True)+'">'+escape(m[1])+'</a>')
    text=re.sub(r'\[([^\]\n]+)\]\(([^\s)]+)\)',link,text)
    text=escape(text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<em>\1</em>',text)
    return re.sub(r'\x00(\d+)\x00',lambda m:tokens[int(m[1])],text)

def render(text):
    lines=text.replace('\r\n','\n').split('\n');out=[];i=0
    def special(line):return bool(re.match(r'^\s*(#{1,6}\s|```|~~~|[-*+]\s|\d+[.)]\s|>\s)',line))
    def cells(line):return [c.strip() for c in line.strip().strip('|').split('|')]
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        fence=re.match(r'^\s*(```+|~~~+)(.*)$',line)
        if fence:
            marker=fence[1];code=[];i+=1
            while i<len(lines) and not lines[i].strip().startswith(marker):code.append(lines[i]);i+=1
            if i==len(lines):raise ValueError('Unclosed Markdown code fence')
            out.append('<pre><code>'+escape('\n'.join(code))+'</code></pre>');i+=1;continue
        heading=re.match(r'^\s*(#{1,6})\s+(.+?)\s*#*$',line)
        if heading:
            n=min(5,max(3,len(heading[1])));out.append(f'<h{n}>'+inline(heading[2])+f'</h{n}>');i+=1;continue
        if i+1<len(lines) and '|' in line and re.fullmatch(r'\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*',lines[i+1]):
            headers=cells(line);i+=2;rows=[]
            while i<len(lines) and lines[i].strip() and '|' in lines[i]:rows.append(cells(lines[i]));i+=1
            out.append('<table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>');continue
        li=re.match(r'^\s*([-*+]|\d+[.)])\s+(.+)$',line)
        if li:
            ordered=li[1][0].isdigit();tag='ol' if ordered else 'ul';items=[]
            start=int(re.match(r'\d+',li[1])[0]) if ordered else 1
            while i<len(lines):
                m=re.match(r'^\s*([-*+]|\d+[.)])\s+(.+)$',lines[i])
                if not m or m[1][0].isdigit()!=ordered:break
                items.append('<li>'+inline(m[2])+'</li>');i+=1
            out.append('<'+tag+(' start="'+str(start)+'"' if ordered and start!=1 else '')+'>'+''.join(items)+'</'+tag+'>');continue
        if line.lstrip().startswith('> '):
            parts=[]
            while i<len(lines) and lines[i].lstrip().startswith('> '):parts.append(lines[i].lstrip()[2:]);i+=1
            out.append('<blockquote><p>'+inline(' '.join(parts))+'</p></blockquote>');continue
        paragraph=[line.strip()];i+=1
        while i<len(lines) and lines[i].strip() and not special(lines[i]):
            if i+1<len(lines) and '|' in lines[i] and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):break
            paragraph.append(lines[i].strip());i+=1
        out.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '\n'.join(out)
