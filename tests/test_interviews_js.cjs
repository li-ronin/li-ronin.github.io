/* Dependency-free behavior checks. DOM shim tests logic, not browser layout. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'data/interviews.json')));
class Element {
  constructor(value = '') { this.value = value; this.hidden = false; this.listeners = {}; this.textContent = ''; this.open = false; }
  addEventListener(type, callback) { this.listeners[type] = callback; }
  focus() {} scrollIntoView() {}
}
const fields = ['question-search','category-filter','tag-filter','difficulty-filter','role-filter','audience-filter'];
const els = Object.fromEntries([...fields,'interview-filters','result-count','no-results','expand-all','collapse-all'].map(id => [id,new Element()]));
const cards = data.questions.map(q => {
  const card = new Element();
  card.id = q.id;
  card.dataset = {category:q.category, difficulty:String(q.difficulty),roles:q.roles.join('|'),audience:q.audience.join('|'),tags:q.tags.join('|'),search:[q.id,q.title,...q.tags,...q.knowledge,...q.extensions,...q.followups].join(' ').toLowerCase()};
  const details = new Element();card.querySelector = () => details;
  return card;
});
const groups = [...new Set(data.questions.map(q => q.category))].map(category => {
  const group = new Element(); const count = new Element();
  group.querySelectorAll = () => cards.filter(c => c.dataset.category === category);
  group.querySelector = () => count;return group;
});
const buttons = cards.flatMap(c => c.dataset.tags.split('|').map(tag => {const b=new Element();b.dataset={tag};b.disabled=true;return b;}));
const listeners = {};
const window = {location:{href:'https://example.com/post/archive.html',search:'',hash:''},history:{replaceState:(_,__,url)=>{window.location.href=url.href;window.location.search=url.search;window.location.hash=url.hash;}},addEventListener:(type,cb)=>{listeners[type]=cb;}};
els['interview-filters'].reset = () => { fields.forEach(f => els[f].value=''); if(els['interview-filters'].listeners.reset) els['interview-filters'].listeners.reset(); };
const document = {getElementById:id=>els[id],querySelectorAll:selector=>({'.question':cards,'.question-group':groups,'.knowledge-tag':buttons}[selector])};
vm.runInNewContext(fs.readFileSync(path.join(root,'assets/interviews.js'),'utf8'),{document,window,URL,URLSearchParams,setTimeout:fn=>fn()});
const visible=()=>cards.filter(c=>!c.hidden);
const change=(id,value)=>{els[id].value=value;els['interview-filters'].listeners.input();};
assert.equal(visible().length,data.questions.length);
change('question-search','nonexistent-xyz');assert.equal(visible().length,0);assert.equal(els['no-results'].hidden,false);
els['interview-filters'].reset();assert.equal(visible().length,data.questions.length);
change('tag-filter','上下文压缩');assert.ok(visible().length>0);assert.ok(visible().every(c=>c.dataset.tags.split('|').includes('上下文压缩')));
els['expand-all'].listeners.click();assert.ok(visible().every(c=>c.querySelector().open));
els['collapse-all'].listeners.click();assert.ok(visible().every(c=>!c.querySelector().open));
change('difficulty-filter','3');assert.ok(visible().every(c=>c.dataset.difficulty==='3'));
els['interview-filters'].reset();change('category-filter','RAG与知识工程');assert.ok(visible().length>0);assert.ok(visible().every(c=>c.dataset.category==='RAG与知识工程'));
els['interview-filters'].reset();buttons[0].listeners.click();assert.equal(els['tag-filter'].value,buttons[0].dataset.tag);assert.ok(buttons.every(b=>!b.disabled));
window.location.search='?q=GraphRAG';listeners.popstate();assert.ok(visible().length>0);assert.ok(visible().every(c=>c.dataset.search.includes('graphrag')));
window.location.hash='#'+cards[0].id;listeners.hashchange();assert.equal(cards[0].hidden,false);assert.equal(cards[0].querySelector().open,true);assert.equal(els['question-search'].value,'');
console.log('PASS: offline filter, reset, empty state, combined facets, expand/collapse, tag, URL restoration and deep-link logic ('+cards.length+' questions). Not a browser/layout test.');
