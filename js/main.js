/* Keep the standalone homepage and indexes outside the legacy Swup lifecycle. */
(() => {
  const standalonePaths = new Set(['/', '/blog', '/notes']);
  const normalize = (path) => path.replace(/index\.html$/, '').replace(/\/+$/, '') || '/';

  const syncNavigation = () => {
    document.querySelectorAll('.home-paginator a[href]').forEach((link) => {
      const url = new URL(link.href, location.href);
      if (url.origin === location.origin && normalize(url.pathname) === '/') {
        link.href = '/blog/' + url.search + url.hash;
      }
    });

    const header = document.querySelector('.main-content-header');
    if (header && !header.querySelector('[data-academic-navigation]')) {
      const nav = document.createElement('nav');
      nav.setAttribute('data-academic-navigation', '');
      nav.setAttribute('aria-label', '个人主页与写作导航');
      nav.style.cssText = 'display:flex;flex-wrap:wrap;gap:20px;max-width:1000px;margin:12px auto;padding:0 20px;font-size:14px;';
      [['主页', '/'], ['Blog', '/blog/'], ['Notes', '/notes/'], ['归档', '/archives/']].forEach(([label, href]) => {
        const link = document.createElement('a');
        link.textContent = label;
        link.href = href;
        nav.appendChild(link);
      });
      header.appendChild(nav);
    }

    document.querySelectorAll('a[href]').forEach((link) => {
      const url = new URL(link.href, location.href);
      if (url.origin === location.origin && standalonePaths.has(normalize(url.pathname))) {
        link.setAttribute('data-no-swup', '');
      }
    });
  };

  // Capture before Swup's delegated handler, preserving modified/new-tab clicks.
  document.addEventListener('click', (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target instanceof Element ? event.target.closest('a[href]') : null;
    if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || !standalonePaths.has(normalize(url.pathname))) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    location.assign(url.href);
  }, true);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncNavigation);
  else syncNavigation();
  if (typeof swup !== 'undefined') swup.on('pageView', syncNavigation);
})();

/* Legacy Redefine initialization. Article rendering and URLs stay unchanged. */
window.addEventListener('DOMContentLoaded', () => {
  Global.themeInfo = {
    theme: `Redefine v${Global.theme_config.version}`,
    author: 'EvanNotFound',
    repository: 'https://github.com/EvanNotFound/hexo-theme-redefine'
  };
  Global.localStorageKey = 'REDEFINE-THEME-STATUS';
  Global.styleStatus = {
    isExpandPageWidth: false,
    isDark: false,
    fontSizeLevel: 0,
    isOpenPageAside: true
  };
  Global.printThemeInfo = () => {
    console.log(`${Global.themeInfo.theme} — ${Global.themeInfo.repository}`);
  };
  Global.setStyleStatus = () => {
    localStorage.setItem(Global.localStorageKey, JSON.stringify(Global.styleStatus));
  };
  Global.getStyleStatus = () => {
    let temp = localStorage.getItem(Global.localStorageKey);
    if (temp) {
      temp = JSON.parse(temp);
      for (let key in Global.styleStatus) Global.styleStatus[key] = temp[key];
      return temp;
    }
    return null;
  };
  Global.refresh = () => {
    Global.initUtils();
    navbarShrink.init();
    if (Global.data_config.masonry) Global.initMasonry();
    Global.initModeToggle();
    Global.initBackToTop();
    if (Global.theme_config.home_banner.subtitle.text.length !== 0 && location.pathname === Global.hexo_config.root) {
      Global.initTyped('subtitle');
    }
    if (Global.theme_config.plugins.mermaid.enable === true) Global.initMermaid();
    if (Global.theme_config.navbar.search.enable === true) Global.initLocalSearch();
    if (Global.theme_config.articles.code_block.copy === true) Global.initCopyCode();
    if (Global.theme_config.articles.lazyload === true) Global.initLazyLoad();
  };
  Global.printThemeInfo();
  Global.refresh();
});
