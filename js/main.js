/* Progressive enhancements for the academic reading layout.
 * Existing post HTML and URLs remain the content source of truth.
 * No remote libraries, theme settings, tracking, or HTML string interpolation. */
(() => {
  'use strict';
  const FULL_NAME = '李可涵 Khan Li';
  const notePath = '/post/摘录与感悟.html';
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const link = (text, href, className = '') => {
    const node = make('a', className, text);
    node.setAttribute('href', href);
    return node;
  };
  const normalizedPath = () => {
    try { return decodeURIComponent(location.pathname); }
    catch (_) { return location.pathname; }
  };

  function enhanceReading() {
    if (document.documentElement.dataset.academicReading) return;
    document.documentElement.dataset.academicReading = 'true';
    document.documentElement.lang = 'zh-CN';

    // The static HTML still includes legacy helper definitions. Do not start them.
    for (const name of ['initTOC', 'initTocToggle', 'footerRuntime']) {
      if (typeof window[name] === 'function') {
        window.removeEventListener('DOMContentLoaded', window[name]);
      }
    }
    if (typeof swup !== 'undefined' && typeof swup.destroy === 'function') swup.destroy();
    document.documentElement.classList.remove('is-animating', 'is-changing', 'is-leaving', 'is-rendering');
    if (typeof Global !== 'undefined') {
      Global.utils = {};
      Global.refresh = () => {};
    }

    const path = normalizedPath();
    const isNote = path === notePath;
    const content = document.querySelector('.article-content.markdown-body');
    const current = content ? (isNote ? '/notes/' : '/blog/') : '/archives/';
    const header = document.querySelector('.main-content-header');
    if (header) {
      const nav = make('nav', 'site-nav');
      nav.setAttribute('aria-label', '站点导航');
      nav.append(link(FULL_NAME, '/', 'site-name'));
      const items = make('div', 'site-nav-links');
      for (const [name, href] of [['Home', '/'], ['Blog', '/blog/'], ['Notes', '/notes/'], ['归档', '/archives/']]) {
        const item = link(name, href);
        if (href === current) item.setAttribute('aria-current', 'page');
        items.append(item);
      }
      nav.append(items);
      header.replaceChildren(nav);
    }

    const main = document.querySelector('.main-content-body');
    if (main) {
      main.id = 'reading-main';
      main.tabIndex = -1;
      document.body.prepend(link('跳到正文', '#reading-main', 'skip-link'));
    }
    const footer = document.querySelector('.footer');
    if (footer) {
      // Keep hidden legacy timer nodes for backwards-compatible external helpers.
      const small = make('div', 'site-footer');
      small.append(make('span', '', '© ' + FULL_NAME), link('GitHub', 'https://github.com/li-ronin'));
      footer.append(small);
    }
    for (const anchor of document.querySelectorAll('.home-paginator a[href]')) {
      const target = new URL(anchor.href, location.href);
      if (target.origin === location.origin && /^\/(?:index\.html)?$/.test(target.pathname)) {
        anchor.href = '/blog/' + target.search + target.hash;
      }
    }

    if (!content) return;
    const title = document.querySelector('.article-title h1');
    if (title) document.title = title.textContent.trim() + ' · ' + FULL_NAME;
    const metadata = document.querySelector('.article-header');
    if (metadata) {
      const compact = make('div', 'reading-meta');
      compact.append(link(FULL_NAME, '/'));
      const dates = metadata.querySelectorAll('.article-date .desktop');
      dates.forEach((date, index) => {
        const value = date.textContent.trim().slice(0, 10);
        if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return;
        const time = make('time', '', (index ? '更新于 ' : '') + value);
        time.dateTime = value;
        compact.append(time);
      });
      const tags = make('span', 'reading-tags');
      metadata.querySelectorAll('.article-tags a').forEach((a) => tags.append(a.cloneNode(true)));
      if (tags.childNodes.length) compact.append(tags);
      metadata.replaceWith(compact);
    }
    // Promote the old data-src loader to browser-native images without changing the files.
    for (const image of content.querySelectorAll('img[data-src]')) {
      const source = image.getAttribute('data-src');
      if (!source) continue;
      image.loading = 'lazy';
      image.decoding = 'async';
      image.src = source;
      image.removeAttribute('lazyload');
      image.removeAttribute('data-src');
    }
    const headings = [...content.querySelectorAll('h2[id], h3[id]')];
    if (headings.length > 1) {
      const toc = make('details', 'reading-toc');
      toc.append(make('summary', '', '目录 · Contents'));
      const list = make('ol');
      headings.forEach((heading) => {
        const item = make('li', heading.tagName === 'H3' ? 'toc-subheading' : '');
        item.append(link(heading.textContent.trim(), '#' + encodeURIComponent(heading.id)));
        list.append(item);
      });
      toc.append(list);
      content.before(toc);
    }
    for (const table of content.querySelectorAll('table')) {
      if (table.closest('.highlight')) continue;
      const scroll = make('div', 'table-scroll');
      scroll.tabIndex = 0;
      scroll.setAttribute('role', 'region');
      scroll.setAttribute('aria-label', '表格，可横向滚动');
      table.before(scroll);
      scroll.append(table);
    }
    for (const block of content.querySelectorAll('.highlight-container')) {
      const pre = block.querySelector('td.code pre');
      if (!pre) continue;
      const scroll = block.querySelector('.highlight');
      if (scroll) {
        scroll.tabIndex = 0;
        scroll.setAttribute('role', 'region');
        scroll.setAttribute('aria-label', (block.dataset.rel || '') + ' 代码，可横向滚动');
      }
      const button = make('button', 'copy-code', '复制');
      button.type = 'button';
      button.setAttribute('aria-label', '复制代码');
      button.setAttribute('aria-live', 'polite');
      button.addEventListener('click', async () => {
        try {
          if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
          // Copy only code, never the gutter line numbers or the toolbar.
          await navigator.clipboard.writeText(pre.innerText.replace(/\n$/, ''));
          button.textContent = '已复制';
        } catch (_) {
          const selection = window.getSelection();
          if (selection) {
            const range = document.createRange();
            range.selectNodeContents(pre);
            selection.removeAllRanges();
            selection.addRange(range);
          }
          button.textContent = '已选中，请复制';
        }
        window.setTimeout(() => { button.textContent = '复制'; }, 2400);
      });
      block.append(button);
    }
    const article = document.querySelector('.article-content-container');
    if (article) article.append(link(isNote ? '← 返回随笔目录' : '← 返回技术博客', isNote ? '/notes/' : '/blog/', 'reading-return'));
    // The existing note is a synchronous fallback; future categories follow the index data.
    fetch(new URL('/data/writing.json', document.baseURI))
      .then((response) => response.ok ? response.json() : [])
      .then((entries) => {
        if (!Array.isArray(entries)) return;
        const entry = entries.find((item) => {
          try { return decodeURIComponent(item.url) === path; } catch (_) { return false; }
        });
        if (!entry) return;
        const note = entry.kind === 'note';
        const destination = note ? '/notes/' : '/blog/';
        document.querySelectorAll('.site-nav-links a').forEach((a) => {
          if (a.getAttribute('href') === destination) a.setAttribute('aria-current', 'page');
          else a.removeAttribute('aria-current');
        });
        const back = document.querySelector('.reading-return');
        if (back) {
          back.href = destination;
          back.textContent = note ? '← 返回随笔目录' : '← 返回技术博客';
        }
      }).catch(() => {}); // Article text and navigation never depend on this request.
    // Native anchors, browser history and modified clicks work without a router.
  }

  if (document.readyState === 'loading') window.addEventListener('DOMContentLoaded', enhanceReading, { once: true });
  else enhanceReading();
})();
