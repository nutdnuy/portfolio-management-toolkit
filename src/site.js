(() => {
  const themeButton=document.querySelector('#theme-button');
  function labelTheme(){const dark=document.documentElement.dataset.theme==='dark';themeButton.querySelector('span').textContent=dark?'Light theme':'Dark theme';themeButton.setAttribute('aria-label',`Switch to ${dark?'light':'dark'} theme`);}
  labelTheme();themeButton.addEventListener('click',()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem('pmt-theme',next);}catch{}labelTheme();});
  const menu=document.querySelector('#menu-button');menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Close navigation':'Open navigation');document.querySelector('#sidebar').classList.toggle('open',open);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu.getAttribute('aria-expanded')==='true'){menu.click();menu.focus();}});
  const dialog=document.querySelector('#search-dialog'),input=document.querySelector('#search-input'),results=document.querySelector('#search-results'),status=document.querySelector('#search-status');
  function search(){const q=input.value.trim().toLocaleLowerCase();const matches=(window.PMTSearch||[]).filter(x=>(x.title+' '+x.text).toLocaleLowerCase().includes(q)).slice(0,18);results.replaceChildren();status.textContent=q?`${matches.length}${matches.length===18?'+':''} results`:'Explore pages or type a keyword';for(const item of (q?matches:(window.PMTSearch||[]).filter(x=>!x.url.includes('#')))){const a=document.createElement('a'),title=document.createElement('strong'),label=document.createElement('span');a.href=item.url;title.textContent=item.title;label.textContent=item.section;a.append(title,label);results.append(a);}if(q&&!matches.length)status.textContent='No results · ลองค้นหาคำอื่น เช่น floor หรือ CPPI';}
  function openSearch(){dialog.showModal();search();input.focus();}
  document.querySelector('#search-button').addEventListener('click',openSearch);document.querySelector('#close-search').addEventListener('click',()=>dialog.close());input.addEventListener('input',search);
  document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();dialog.open?dialog.close():openSearch();}});
  results.addEventListener('click',e=>{if(e.target.closest('a'))dialog.close();});
  dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dialog.close();}});
  dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
})();
