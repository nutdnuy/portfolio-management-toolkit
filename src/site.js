(() => {
  const themeButton = document.querySelector('#theme-button');
  function labelTheme() {
    themeButton.textContent = document.documentElement.dataset.theme === 'light' ? 'พื้นหลังมืด' : 'พื้นหลังสว่าง';
  }
  labelTheme();
  themeButton.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('pmt-book-theme', next); } catch {}
    labelTheme();
  });
  document.querySelector('#print-button').addEventListener('click', () => window.print());
  const menu = document.querySelector('#menu-button');
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('menu-open', open);
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { menu.click(); menu.focus(); }
  });
  const dialog = document.querySelector('#search-dialog');
  const input = document.querySelector('#search-input');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  function search() {
    const q = input.value.trim().toLocaleLowerCase();
    const matches = (window.PMTSearch || []).filter(x => (x.title + ' ' + x.text).toLocaleLowerCase().includes(q)).slice(0, 20);
    results.replaceChildren();
    status.textContent = q ? `พบ ${matches.length}${matches.length === 20 ? '+' : ''} ผลลัพธ์` : 'ค้นหาได้ทั้งคำภาษาไทยและภาษาอังกฤษ';
    for (const item of (q ? matches : (window.PMTSearch || []).filter(x => !x.url.includes('#')))) {
      const a = document.createElement('a'), title = document.createElement('strong'), label = document.createElement('small');
      a.href = item.url; title.textContent = item.title; label.textContent = item.section;
      a.append(label, title); results.append(a);
    }
    if (q && !matches.length) status.textContent = 'ไม่พบผลลัพธ์ ลองค้นหาคำอื่น เช่น Floor หรือ CPPI';
  }
  function openSearch() { dialog.showModal(); search(); input.focus(); }
  document.querySelector('#search-button').addEventListener('click', openSearch);
  document.querySelector('#close-search').addEventListener('click', () => dialog.close());
  input.addEventListener('input', search);
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); dialog.open ? dialog.close() : openSearch(); }
  });
  results.addEventListener('click', e => { if (e.target.closest('a')) dialog.close(); });
  dialog.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); dialog.close(); } });
  dialog.addEventListener('click', e => {
    if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); }
  });
  const query = document.querySelector('#glossary-query');
  if (query) {
    const terms = [...document.querySelectorAll('.glossary-term')];
    const report = document.querySelector('#glossary-status');
    function filter() {
      const q = query.value.trim().toLocaleLowerCase(); let visible = 0;
      for (const term of terms) { const match = term.textContent.toLocaleLowerCase().includes(q); term.hidden = !match; if (match) visible++; }
      for (const group of document.querySelectorAll('.glossary-group')) group.hidden = ![...group.querySelectorAll('.glossary-term')].some(term => !term.hidden);
      report.textContent = visible ? `แสดง ${visible} จาก ${terms.length} คำ` : 'ไม่พบคำศัพท์ ลองค้นหาคำอื่น';
    }
    query.addEventListener('input', filter);
    function revealAnchor() {
      if (!location.hash) return;
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) { query.value = ''; filter(); target.scrollIntoView(); }
    }
    filter(); window.addEventListener('hashchange', revealAnchor); revealAnchor();
  }
})();
