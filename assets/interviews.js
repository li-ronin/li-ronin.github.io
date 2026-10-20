/* Progressive enhancement: complete question content is in the static HTML. */
(() => {
  'use strict';
  const form = document.getElementById('interview-filters');
  if (!form) return;
  const cards = Array.from(document.querySelectorAll('.question'));
  const groups = Array.from(document.querySelectorAll('.question-group'));
  const fields = {q: 'question-search', category: 'category-filter', tag: 'tag-filter', difficulty: 'difficulty-filter', role: 'role-filter', audience: 'audience-filter'};
  const controls = Object.fromEntries(Object.entries(fields).map(([key, id]) => [key, document.getElementById(id)]));
  const includes = (card, field, value) => !value || card.dataset[field].split('|').includes(value);
  function apply(updateUrl = true) {
    const v = Object.fromEntries(Object.entries(controls).map(([key, control]) => [key, control.value.trim()]));
    const words = v.q.toLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const card of cards) {
      const match = words.every(w => card.dataset.search.includes(w)) && (!v.category || card.dataset.category === v.category) && (!v.difficulty || card.dataset.difficulty === v.difficulty) && includes(card, 'tags', v.tag) && includes(card, 'roles', v.role) && includes(card, 'audience', v.audience);
      card.hidden = !match;
      if (match) count++;
    }
    for (const group of groups) {
      const visible = Array.from(group.querySelectorAll('.question')).filter(card => !card.hidden).length;
      group.hidden = !visible;
      group.querySelector('.group-count').textContent = `${visible} 题`;
    }
    document.getElementById('result-count').textContent = `显示 ${count} / ${cards.length} 道归并题，按领域与难度排列。`;
    document.getElementById('no-results').hidden = count > 0;
    if (updateUrl) {
      const url = new URL(window.location.href);
      for (const key of Object.keys(controls)) {
        if (v[key]) url.searchParams.set(key, v[key]); else url.searchParams.delete(key);
      }
      window.history.replaceState(null, '', url);
    }
  }
  function readUrl() {
    const params = new URLSearchParams(window.location.search);
    for (const [key, control] of Object.entries(controls)) control.value = params.get(key) || '';
    apply(false);
  }
  function revealHash() {
    const id = window.location.hash.slice(1);
    const card = cards.find(card => card.id === id);
    if (!card) return;
    if (card.hidden) { form.reset(); apply(); }
    card.querySelector('details').open = true;
    card.scrollIntoView({block: 'start'});
  }
  form.hidden = false;
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', () => apply());
  form.addEventListener('change', () => apply());
  form.addEventListener('reset', () => setTimeout(() => apply(), 0));
  document.querySelectorAll('.knowledge-tag').forEach(button => {
    button.disabled = false;
    button.addEventListener('click', () => {
    controls.tag.value = button.dataset.tag;
    apply();
    controls.tag.focus({preventScroll: true});
    form.scrollIntoView({block: 'start'});
    });
  });
  document.getElementById('expand-all').addEventListener('click', () => cards.filter(card => !card.hidden).forEach(card => { card.querySelector('details').open = true; }));
  document.getElementById('collapse-all').addEventListener('click', () => cards.filter(card => !card.hidden).forEach(card => { card.querySelector('details').open = false; }));
  window.addEventListener('popstate', () => { readUrl(); revealHash(); });
  window.addEventListener('hashchange', revealHash);
  readUrl();
  revealHash();
})();
