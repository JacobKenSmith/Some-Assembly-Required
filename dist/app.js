'use strict';
const $=s=>document.querySelector(s);
const E=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const byId=id=>DOCUMENTS.find(d=>d.id===id);
let group='campaign',primary='crash',secondary=null,notes=true,indexMode='objects',zoom=100,toastTimer;
const params=new URLSearchParams(location.search);
if(DOSSIERS.some(g=>g.id===params.get('dossier')))group=params.get('dossier');
primary=DOSSIERS.find(g=>g.id===group).docs[0];
if(byId(params.get('source')))primary=params.get('source');
if(byId(params.get('compare'))&&params.get('compare')!==primary)secondary=params.get('compare');
function notify(s){$('#toast').textContent=s;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),2200)}
function updateUrl(){const p=new URLSearchParams({dossier:group,source:primary});if(secondary)p.set('compare',secondary);history.replaceState(null,'','?'+p+(location.hash||''))}
function citation(d){return `${d.author}. “${d.sourceTitle}.” ${d.outlet}, ${d.date}. ${d.url} [${d.carrier}; ${d.locator}.]`}
function panel(d){return `<article class="reading-panel" aria-label="${E(d.title)}"><header class="document-head"><p class="eyebrow">${E(d.kind)} / ${E(d.date)}</p><h4>${E(d.title)}</h4><p class="credit">${E(d.author)}<br>${E(d.outlet)}</p></header><div class="document-body ${d.id==='crash'?'graphic':''}">${d.image?`<button class="scan-button" data-image="${d.id}" aria-label="Enlarge ${E(d.title)}"><img src="${d.image}" alt="${E(d.title)} — ${E(d.carrier)}"><span>Inspect image +</span></button>`:`<div class="excerpt-sheet"><p class="eyebrow">TYPESET EXCERPT · NOT A FACSIMILE</p><blockquote>${E(d.quote)}</blockquote><p class="sheet-author">${E(d.author.toUpperCase())}<br>${E(d.date)}</p></div>`}</div>${d.imageCaption?`<p class="image-caption">${E(d.imageCaption)}</p>`:''}<div class="annotations">${d.image?`<div class="annotation-block"><h5>EXCERPT</h5><p>“${E(d.quote)}”</p></div>`:''}<div class="annotation-block"><h5>01 / WHAT IS SELECTED</h5><p>${E(d.selects)}</p></div><div class="annotation-block"><h5>02 / WHAT IS MADE OF IT</h5><p>${E(d.argument)}</p></div></div><details class="source-details"><summary>Context & provenance</summary><p>${E(d.context)}</p><dl><dt>Source title</dt><dd>${E(d.sourceTitle)}</dd><dt>Carrier</dt><dd>${E(d.carrier)}</dd><dt>Location</dt><dd>${E(d.locator)}</dd><dt>Evidence</dt><dd>${E(d.verification)}</dd></dl></details><div class="source-footer"><a href="${E(d.url)}" target="_blank" rel="noopener">Read the source ↗</a><button data-copy="${d.id}">Copy citation</button></div></article>`}
function render(){const g=DOSSIERS.find(g=>g.id===group),d=byId(primary);
 $('#dossiers').innerHTML=DOSSIERS.map(x=>`<button class="dossier-tab" data-group="${x.id}" aria-selected="${group===x.id}" aria-label="${x.number}: ${E(x.title)}"><small>${x.number}<span>${x.period}</span></small><strong>${E(x.title)}</strong></button>`).join('');
 $('#dossier-period').textContent=`DOSSIER ${g.number} / ${g.period}`;$('#dossier-title').textContent=g.subtitle;$('#dossier-description').textContent=g.intro;$('#dossier-question').textContent=g.question;$('#source-count').textContent=`${g.docs.length} SOURCES`;
 $('#source-drawer').innerHTML=g.docs.map(id=>{let x=byId(id);return `<div class="source-choice ${id===primary||id===secondary?'is-current':''}"><button class="open-source" data-open="${id}"><small>${E(x.kind.toUpperCase())} · ${E(x.date)}</small><strong>${E(x.title)}</strong><span class="source-author">${E(x.author)}</span></button><button class="compare-source" data-compare="${id}" ${id===primary?'disabled':''}>${id===secondary?'Remove from comparison −':id===primary?'Reading now':'Place alongside +'}</button></div>`}).join('');
 $('#comparison-controls').innerHTML=`<label for="compare-select">COMPARE WITH <select id="compare-select"><option value="">Choose another source…</option>${DOCUMENTS.filter(x=>x.id!==primary).map(x=>`<option value="${x.id}" ${secondary===x.id?'selected':''}>${E(x.author)} · ${E(x.title)}</option>`).join('')}</select></label>${secondary?'<button id="close-compare">Return to one source ×</button>':`<button data-compare="${d.pair}">Suggested pairing ↗</button>`}`;
 $('#reading-panels').classList.toggle('paired',!!secondary);$('#reading-panels').innerHTML=panel(d)+(secondary?panel(byId(secondary)):'');$('.reading-area').classList.toggle('hide-annotations',!notes);
 const isDirect=(primary==='fulano'&&secondary==='eccles')||(primary==='eccles'&&secondary==='fulano');
 const suggested=secondary&&(d.pair===secondary||byId(secondary).pair===primary);
 $('#comparison-note').innerHTML=`<p class="eyebrow">${secondary?(isDirect?'DOCUMENTED RESPONSE':suggested?'CURATED COMPARISON':'YOUR COMPARISON'):'READING ACROSS SOURCES'}</p><p>${secondary&&!suggested&&!isDirect?'These objects have been placed together for comparison. Their proximity here does not establish a direct reply, shared affiliation, or historical influence. Compare their selections, speakers, and publication contexts.':E(d.relation)}</p>`;
 $('#toggle-notes').textContent=notes?'Annotations on':'Annotations off';$('#toggle-notes').setAttribute('aria-pressed',String(notes));updateUrl();
}
function openDoc(id,scroll=true){if(!byId(id))return;if(!DOSSIERS.find(g=>g.id===group).docs.includes(id))group=DOSSIERS.find(g=>g.docs.includes(id)).id;primary=id;if(secondary===id)secondary=null;render();if(scroll)$('#worktable').scrollIntoView({behavior:'smooth'})}
function showArchive(mode='objects'){indexMode=mode;$('#archive-search').value='';renderIndex();$('#archive-dialog').showModal()}
function renderIndex(){const q=$('#archive-search').value.toLowerCase().trim();document.querySelectorAll('[data-index]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.index===indexMode)));let items;
 if(indexMode==='objects'){items=DOCUMENTS.filter(d=>[d.title,d.author,d.date,d.outlet,d.quote,d.kind].join(' ').toLowerCase().includes(q));$('#index-note').textContent='Selected exhibit objects. Open a record to read it on the worktable; provenance accompanies each source.';$('#index-results').innerHTML=items.map(d=>`<div class="index-row"><small>${E(d.kind)}<br>${d.year}</small><div><h3>${E(d.title)}</h3><p>${E(d.author)} · ${E(d.outlet)}</p></div><button data-index-open="${d.id}">Read ↗</button></div>`).join('')}
 else{items=NEWS_INDEX.filter(d=>(d.id+' '+d.title).toLowerCase().includes(q));$('#index-note').textContent='196 PDF pages, not 196 unique articles. Headers are OCR-derived. “Attached PDF” requires access to the research files; PDF page numbers refer to each bundle.';$('#index-results').innerHTML=items.map(d=>`<div class="index-row news-row"><small>${d.id}<br>PDF p. ${d.page}</small><div><h3>${E(d.title)}</h3></div><div>${d.url?`<a href="${E(d.url)}" target="_blank" rel="noopener">Newspaper ↗</a>`:''}<a href="${E(d.attachment)}" target="_blank" rel="noopener">Attached PDF ↗</a></div></div>`).join('')}
 if(!items.length)$('#index-results').innerHTML='<p class="empty">No sources match this search. Try a publication, author, or year.</p>';$('#index-count').textContent=`${items.length} ${indexMode==='objects'?'objects':'pages'}`;
}
function showImage(id){const d=byId(id);$('#large-image').src=d.image;$('#large-image').alt=`${d.title}, ${d.outlet}, ${d.date}`;$('#image-label').textContent=`${d.title} · ${d.date}`;zoom=100;setZoom();$('#image-dialog').showModal()}
function setZoom(){ $('#large-image').style.width=zoom+'%';$('#zoom-level').textContent=zoom+'%';$('#zoom-out').disabled=zoom<=50;$('#zoom-in').disabled=zoom>=250 }
document.addEventListener('click',async e=>{const b=e.target.closest('button');if(!b)return;
 if(b.dataset.group){group=b.dataset.group;primary=DOSSIERS.find(g=>g.id===group).docs[0];secondary=null;render();return}
 if(b.dataset.open){openDoc(b.dataset.open,!b.closest('.source-rail'));return}
 if(b.dataset.compare){const id=b.dataset.compare;if(id===primary)return;secondary=secondary===id?null:id;render();return}
 if(b.dataset.image){showImage(b.dataset.image);return}
 if(b.hasAttribute('data-close')){b.closest('dialog').close();return}
 if(b.dataset.index){indexMode=b.dataset.index;$('#archive-search').value='';renderIndex();return}
 if(b.dataset.indexOpen){$('#archive-dialog').close();openDoc(b.dataset.indexOpen);return}
 if(b.dataset.copy){try{await navigator.clipboard.writeText(citation(byId(b.dataset.copy)));notify('Citation copied')}catch{notify('Copy unavailable. The source link and citation details remain below the document.')}return}
 if(b.dataset.action==='archive'||b.id==='browse-all'){showArchive();return}
 if(b.dataset.action==='about'){$('#about-dialog').showModal();return}
 if(b.dataset.action==='letters'){group='magazines';primary='eccles';secondary='tedits';render();$('#worktable').scrollIntoView({behavior:'smooth'});return}
 if(b.id==='close-compare'){secondary=null;render()}
 if(b.id==='toggle-notes'){notes=!notes;render()}
 if(b.id==='reset-table'){primary=DOSSIERS.find(g=>g.id===group).docs[0];secondary=null;notes=true;render();notify('Arrangement reset')}
 if(b.id==='zoom-in'){zoom=Math.min(250,zoom+25);setZoom()}
 if(b.id==='zoom-out'){zoom=Math.max(50,zoom-25);setZoom()}
});
document.addEventListener('change',e=>{if(e.target.id==='compare-select'){secondary=e.target.value||null;render()}});
$('#archive-search').addEventListener('input',renderIndex);
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}}));
render();
