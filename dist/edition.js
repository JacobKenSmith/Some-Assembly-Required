const { paragraphs, sources, annotations, footnotes, baseUrl, sections } = EDITION;
const text = document.querySelector('#text');
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const sourceMap = new Map(sources.map(s => [s.id,s]));
const sourceFor = id => sourceMap.get(id);
const incidence = new Map(paragraphs.map(p => [p.n,annotations.filter(a => a.paras.includes(p.n))]));
const postCache = new Map();
const annotationMap = new Map(annotations.map(a=>[a.id,a]));
const paragraphMap = new Map(paragraphs.map(p=>[p.n,p]));
let active = null;
let currentSection = 'all';
let filter = 'reception';
function included(response) {
  const source=sourceFor(response.source),usenet=source.type==='Usenet',fourchan=source.type==='4chan',repost=source.category==='extended_reproduction';
  return filter==='all'||(filter==='reception'&&!repost)||(filter==='usenet'&&usenet&&!repost)||(filter==='4chan'&&fourchan)||(filter==='reposts'&&repost)||(filter==='published'&&!usenet&&!fourchan);
}
const responsesFor = (number,anchorId) => {
  const ids=anchorId?paragraphMap.get(number)?.anchors.find(a=>a.id===anchorId)?.annotationIds:null;
  return (incidence.get(number)||[]).filter(a=>included(a)&&(!ids||ids.includes(a.id)));
};
const observer = new ResizeObserver(alignNote);

function renderText() {
  closeNote();
  document.querySelector('h1').textContent='Industrial Society and Its Future';
  text.innerHTML=paragraphs.map(paragraph=>{
    const {n}=paragraph,chars=Array.from(paragraph.text),parts=[];let cursor=0;
    for(const anchor of paragraph.anchors||[]){
      const responses=responsesFor(n,anchor.id);
      parts.push(escapeHTML(chars.slice(cursor,anchor.start).join('')));
      const phrase=escapeHTML(chars.slice(anchor.start,anchor.end).join(''));
      parts.push(responses.length?`<a href="#p${n}" role="button" class="phrase" data-anchor="${anchor.id}" aria-expanded="false" aria-controls="responses-${n}" aria-label="Reception notes for this passage in paragraph ${n}, ${responses.length} responses">${phrase}</a>`:phrase);
      cursor=anchor.end;
    }
    parts.push(escapeHTML(chars.slice(cursor).join('')));
    const heading=sections.find(s=>s.start===n);
    return `${heading?`<h2 class="section-heading">${escapeHTML(heading.title)}</h2>`:''}<section class="passage" id="p${n}" aria-label="Paragraph ${n}"><span class="number" aria-hidden="true">${n}</span><p class="primary">${parts.join('')}</p>${responsesFor(n).length?`<aside class="note" id="responses-${n}" aria-label="Reception of paragraph ${n}" hidden><div class="note-content" aria-live="polite"></div><nav class="note-nav" aria-label="Responses"><button type="button" data-step="-1">← Previous</button><span class="note-position"></span><button type="button" data-step="1">Next →</button></nav><label class="response-picker">Response<select aria-label="Choose a reception note"></select></label></aside>`:''}</section>`;
  }).join('');
}
function alignNote() {
  if(!active)return;
  active.note.style.setProperty('--anchor',`${Math.max(0,active.phrase.getBoundingClientRect().top-active.section.getBoundingClientRect().top-12)}px`);
}
function closeNote() {
  if(!active)return;active.note.hidden=true;active.phrase.setAttribute('aria-expanded','false');observer.disconnect();active=null;
}
function passageURL(source,response) {
  if(source.type==='Usenet'||source.type==='4chan')return source.url;
  if(response.passageScan)return response.passageScan;
  return `${source.url}#:~:text=${encodeURIComponent(response.excerpt).replaceAll('-','%2D')}`;
}
function passageMarkup(post,response,number) {
  if(response.engagementParts){
    return response.engagementParts.map(part=>`<span class="quote-relation">${escapeHTML(part.role)}</span>\n${passageMarkup(post,{...response,engagementParts:null,excerptStart:part.start,excerptEnd:part.end},number)}`).join('\n\n[…]\n\n');
  }
  const start=response.excerptStart??0,end=response.excerptEnd??Array.from(post.body).length;
  const matches=post.matches.filter(m=>m.paragraph===number&&m.start>=start&&m.end<=end),parts=[];
  const chars=Array.from(post.body),slice=(a,b)=>chars.slice(a,b).join('');let cursor=start;
  for(const m of matches){if(m.start<cursor)continue;parts.push(escapeHTML(slice(cursor,m.start)));parts.push(`<mark>${escapeHTML(slice(m.start,m.end))}</mark>`);cursor=m.end;}
  parts.push(escapeHTML(slice(cursor,end)));return parts.join('');
}
function renderNote() {
  const state=active;if(!state)return;
  const {index,note,responses}=state,response=responses[index],source=sourceFor(response.source),isUsenet=source.type==='Usenet';
  const kind=isUsenet?(response.engagementParts?'Response to the quoted passage':response.category==='extended_reproduction'?'Extended reproduction':response.inheritedOnly?'Contains an inherited quotation':'Contains a manifesto quotation'):response.kind==='Quotation'?'Quotes the manifesto':response.kind;
  note.querySelector('.note-content').innerHTML=`<header class="source"><strong>${escapeHTML(source.name)}</strong><span><cite>${escapeHTML(source.outlet)}</cite> · ${escapeHTML(source.date)}</span></header>${isUsenet?`<p class="quote-relation">${escapeHTML(kind)}${response.notes?.length?' · includes original note '+response.notes.join(', '):''}</p>`:''}<blockquote class="${isUsenet?'post-quotation':''}" ${isUsenet?'aria-busy="true"':''}>${isUsenet?'Loading the original post…':escapeHTML(response.excerpt)}</blockquote><a href="${escapeHTML(passageURL(source,response))}" target="_blank" rel="noopener">${response.passageScan?'Open the magazine page':'Read the complete source in context'} ↗</a><details><summary>Source details</summary><p><b>${escapeHTML(response.title)}</b><br><i>${escapeHTML(source.title)}</i></p><p>${escapeHTML(kind)} · ${escapeHTML(response.locator)}</p>${isUsenet?`<p>Posted as ${escapeHTML(source.address)}<br>Original date: ${escapeHTML(source.rawDate)}<br>Crossposted groups: ${escapeHTML(source.newsgroups)}</p>`:''}<p>${escapeHTML(source.provenance)}</p><p>Linked to ${response.paras.map(n=>'§'+n).join(', ')}.</p><a href="${escapeHTML(source.url)}" target="_blank" rel="noopener">Open the full source ↗</a>${source.image?`<a href="${escapeHTML(source.image)}" target="_blank" rel="noopener"><img src="${escapeHTML(source.image)}" alt="Magazine page from Fixed Ideas and Letter Bombs" loading="lazy"></a>`:''}</details>`;
  if(source.type==='4chan'){
    note.querySelector('.note-content').innerHTML=`<header class="source"><strong>${escapeHTML(source.name)}</strong><span><cite>${escapeHTML(source.outlet)}</cite> · ${escapeHTML(source.date)}</span></header><p class="quote-relation">${escapeHTML(response.kind)}</p><div class="post-quotation">${response.quoteExcerpt?`<p class="quote-relation">Quoted in the linked post${response.quotePostIds.length?' · '+response.quotePostIds.map(escapeHTML).join(', '):''}</p><blockquote>${escapeHTML(response.quoteExcerpt)}</blockquote><p class="quote-relation">Response · post ${escapeHTML(response.postId)}</p>`:''}<blockquote>${escapeHTML(response.excerpt)}</blockquote></div><p class="quote-relation">${escapeHTML(response.locator)}</p><a href="${escapeHTML(source.url)}" target="_blank" rel="noopener">Read the complete post and parent context ↗</a><details><summary>Source details</summary><p>${escapeHTML(source.provenance)}</p><p>Linked to ${response.paras.map(n=>'§'+n).join(', ')}.</p><a href="${escapeHTML(source.archiveUrl)}" target="_blank" rel="noopener">Open the archived thread ↗</a></details>`;
  }
  const nav=note.querySelector('.note-nav');nav.hidden=responses.length<2;nav.querySelector('.note-position').textContent=`${index+1} of ${responses.length}`;
  nav.querySelector('[data-step="-1"]').disabled=index===0;nav.querySelector('[data-step="1"]').disabled=index===responses.length-1;
  const picker=note.querySelector('.response-picker');picker.hidden=responses.length<2;
  picker.querySelector('select').innerHTML=responses.map((r,i)=>{const s=sourceFor(r.source);return `<option value="${i}" ${i===index?'selected':''}>${escapeHTML(s.date+' · '+s.name+' · '+r.title+(r.excerptNumber?' · passage '+r.excerptNumber:''))}</option>`;}).join('');
  history.replaceState(null,'',`#${state.section.id}/${response.id}`);alignNote();
  if(isUsenet){
    if(!postCache.has(source.id))postCache.set(source.id,fetch(source.postData).then(r=>{if(!r.ok)throw Error('Could not load source');return r.json();}).catch(e=>{postCache.delete(source.id);throw e;}));
    postCache.get(source.id).then(post=>{
      if(active!==state||state.responses[state.index]!==response)return;
      const block=note.querySelector('blockquote');block.innerHTML=passageMarkup(post,response,Number(state.section.id.slice(1)));block.setAttribute('aria-busy','false');
      // Each bubble preserves one local exchange; the full post is linked separately.
      const mark=block.querySelector('mark');if(mark)block.scrollTop=Math.max(0,mark.offsetTop-block.offsetTop-55);
      alignNote();
    }).catch(()=>{if(active===state&&state.responses[state.index]===response){const block=note.querySelector('blockquote');block.textContent='The post could not be loaded. Use the complete-source link below.';block.setAttribute('aria-busy','false');}});
  }
}
function openNote(section,responseId,anchorId) {
  closeNote();if(!section)return;
  const n=Number(section.id.slice(1)),all=responsesFor(n);
  const target=all.find(a=>a.id===responseId)||all.find(a=>a.source===responseId);
  if(!anchorId){anchorId=paragraphMap.get(n)?.anchors.find(a=>target?a.annotationIds.includes(target.id):a.annotationIds.some(id=>all.some(r=>r.id===id)))?.id;}
  const phrase=section.querySelector(`.phrase[data-anchor="${anchorId}"]`);if(!phrase)return;
  const responses=responsesFor(n,anchorId);if(!responses.length)return;
  const note=section.querySelector('.note');active={section,phrase,note,responses,anchorId,index:Math.max(0,responses.findIndex(r=>r.id===target?.id))};
  note.hidden=false;phrase.setAttribute('aria-expanded','true');renderNote();observer.observe(section);
}
function clearSelection(){closeNote();history.replaceState(null,'',location.pathname+location.search);}
function togglePhrase(phrase){if(active?.phrase===phrase){clearSelection();return;}const prior=phrase.getBoundingClientRect().top;openNote(phrase.closest('.passage'),null,phrase.dataset.anchor);const movement=phrase.getBoundingClientRect().top-prior;if(movement)window.scrollBy(0,movement);}
text.addEventListener('click',event=>{const phrase=event.target.closest('.phrase');if(phrase){event.preventDefault();togglePhrase(phrase);return;}const step=event.target.closest('[data-step]');if(step&&active?.note.contains(step)){active.index+=Number(step.dataset.step);renderNote();}});
text.addEventListener('change',event=>{if(event.target.matches('.response-picker select')&&active){active.index=Number(event.target.value);renderNote();}});
document.addEventListener('keydown',event=>{if(event.key===' '&&event.target.matches('.phrase')){event.preventDefault();if(!event.repeat)togglePhrase(event.target);}else if(event.key==='Escape'&&active){const phrase=active.phrase;clearSelection();phrase.focus({preventScroll:true});}});
const sectionPicker=document.querySelector('#section-picker');sectionPicker.innerHTML=sections.map(s=>`<option value="${s.start}">${escapeHTML(s.title)} · §§${s.start}–${s.end}</option>`).join('')+'<option value="all">Complete text · §§1–232</option>';sectionPicker.value=currentSection;
sectionPicker.insertAdjacentHTML('beforeend','<option value="other">Other writings and passage references</option>');
sectionPicker.addEventListener('change',()=>{currentSection=sectionPicker.value;if(currentSection==='all'){clearSelection();window.scrollTo(0,0);}else if(currentSection==='other'){document.getElementById('other-writings').hidden=false;document.getElementById('other-writings').scrollIntoView({block:'start'});}else{document.getElementById('p'+currentSection)?.scrollIntoView({block:'start'});}});
document.querySelector('#source-filter').addEventListener('change',event=>{const n=active?Number(active.section.id.slice(1)):null,anchor=active?.anchorId;filter=event.target.value;renderText();document.getElementById('other-writings').hidden=!['all','4chan','reception'].includes(filter);if(n)openNote(document.getElementById('p'+n),null,anchor);});
document.querySelector('#base-link').href=baseUrl;
document.querySelector('#footnotes').innerHTML=Object.entries(footnotes).map(([n,note])=>`<p id="fn${n}"><b>${n}.</b> ${escapeHTML(note)}</p>`).join('');
function restoreSelection(){
  const match=/^#(p\d+)(?:\/([a-z0-9-]+))?$/.exec(location.hash);if(!match){closeNote();return;}
  const n=Number(match[1].slice(1)),s=sections.find(s=>n>=s.start&&n<=s.end);if(!s)return;
  sectionPicker.value=String(s.start);
  const linked=annotationMap.get(match[2]);
  if(match[2]&&sourceFor(linked?.source||match[2])?.category==='extended_reproduction'){filter='all';document.querySelector('#source-filter').value=filter;renderText();}
  const section=document.getElementById(match[1]);openNote(section,match[2]);section?.scrollIntoView({block:'start'});
}
function renderOtherWritings(){
  const host=document.getElementById('other-responses');
  host.innerHTML=(EDITION.additionalResponses||[]).map(r=>{const s=sourceFor(r.source);return `<details id="${escapeHTML(r.id)}"><summary>${escapeHTML(s.date+' · '+r.work+' · '+r.kind)}</summary><p class="quote-relation">${escapeHTML(s.outlet+' · Post '+s.id.replace('4chan-',''))}</p>${r.quoteExcerpt?`<p class="quote-relation">Quoted wording in this post or its linked parent</p><blockquote>${escapeHTML(r.quoteExcerpt)}</blockquote>`:''}<p class="quote-relation">Response</p><blockquote>${escapeHTML(r.excerpt)}</blockquote><p class="quote-relation">${escapeHTML(r.mappingNote)}</p><a href="${escapeHTML(s.url)}" target="_blank" rel="noopener">Read the complete post and context ↗</a></details>`;}).join('');
  host.addEventListener('toggle',event=>{if(event.target.open){closeNote();host.querySelectorAll('details[open]').forEach(d=>{if(d!==event.target)d.open=false;});}},true);
}
window.addEventListener('hashchange',restoreSelection);renderText();renderOtherWritings();restoreSelection();
