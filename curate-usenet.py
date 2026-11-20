"""Select actual passage engagement; preserve the untouched raw-post archive."""
from pathlib import Path
import json,re,collections,gzip
from passage_notes import token_spans,anchor_range
ROOT=Path(__file__).resolve().parent;DIST=ROOT/'dist'
# Qualitative source review. The numbers are stable positions in the preserved
# 723-record import, not post/message identifiers or a word-count classifier.
KEEP=set('''1 3 4 7 10 11 12 14 15 30 31 32 34 35 36 37 39 41 42 43 44 45 46 47 48 49 50 52 53 55 56 57 58 59 60 62 63 65 66 67 68 69 71 72 74 75 76 77 78 80 81 83 85 87 93 94 95 96 97 98 103 107 109 110 112 114 115 116 117 118 119 121 122 123 124 125 126 127 128 130 131 132 134 136 137 138 139 140 141 142 143 144 145 146 148 149 150 151 152 154 155 156 157 158 159 160 161 162 163 164 165 167 169 170 171 172 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 193 198 199 200 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 234 235 241 243 245 246 247 249 250 253 258 259 260 261 271 272 277 279 280 281 286 288 292 293 298 300 302 307 309 315 328 330 333 336 337 340 341 343 349 355 356 357 359 360 362 363 364 365 366 367 368 369 370 371 373 375 376 377 379 380 381 382 383 384 385 392 393 394 395 396 398 399 400 401 402 403 404 406 407 408 411 412 413 414 415 416 418 419 420 421 422 423 424 426 427 428 429 431 432 433 434 435 436 437 438 439 440 441 442 443 444 445 446 447 448 453 455 457 458 459 461 462 463 464 465 466 467 468 469 470 471 472 473 478 479 481 482 484 485 486 487 488 490 491 492 493 494 496 497 500 503 517 518 519 520 521 522 524 528 529 532 535 537 538 544 545 549 550 551 552 553 555 556 557 558 559 560 561 562 563 564 566 567 568 569 570 572 583 587 594 599 603 604 629 630 631 633 640 641 643 649 651 653 654 655 657 658 659 670 675 683 711 712 716 720 721 722'''.split());KEEP={int(x) for x in KEEP}-{131,149,150,151,152,293,379,631,654,722}
# Override meaningful preceding context when the earlier splitter displayed only
# the quotation. No standalone repost or signature is rescued by this list.
BRIEF=re.compile(r'(?i)^(?:yes|no|agree|agreed|yuppies|very the matrix|long live FC|hear hear|right|exactly|well said)[.!?\s]*$')
META=re.compile(r'(?i)^(?:\s*(?:[\W\d_]+|[A-Za-z]{1,3})\s*$|.*(?:wrote|writes|said|schrieb)(?: in .*)?:\s*$|in (?:article|message)\b|(?:sent via|share what you know|before you buy|search, read|create your own|http[s]?://|ftp://|mailto:|from:|date:|subject:|newsgroups:|message-id:|organization:|content-length:)|(?:regards|cheers|sincerely|thanks|thank you|best wishes|kind regards|yours truly)[,.!\s]*$|(?:the unabomber manifesto|industrial society and its future|ISAIF|FC|the manifesto|theodore kaczynski)[,.\s]*$)')
QDEPTH=re.compile(r'^\s*(?:(?:[A-Za-z]{1,8})?>|\|>|\||:)')
FOOTER=re.compile(r'(?i)^\s*(?:--\s*$|sent via deja|-----.*posted via|http://www\.deja|share what you know|before you buy)')

def words(s):return re.findall('[A-Za-z]+',s)
def meaningful(s):
 s=s.strip();return bool(BRIEF.fullmatch(s)) or (len(words(s))>=3 and not META.search(s))

def main():
 records=[json.loads(s) for s in (ROOT/'source/usenet-posts.jsonl').read_text().splitlines()]
 data=json.loads(gzip.decompress((ROOT/'source/usenet-review/baseline-edition.json.gz').read_bytes()));original=[a for a in data['annotations'] if a['source'].startswith('usenet-')]
 # Build the reference vocabulary from the reading text and historical matched
 # spellings. This removes unmatched OCR/reflow fragments from reply detection.
 grams=set()
 for text in [p['text'] for p in data['paragraphs']]+[m['quote'] for r in records for m in r['matches'] if m['status']=='included']:
  ws=[t[0] for t in token_spans(text)]
  grams.update(tuple(ws[i:i+8]) for i in range(len(ws)-7))
 ann=[];audit=[];review=[]
 for ri,r in enumerate(records):
  if ri not in KEEP:
   audit.append({'id':r['id'],'included':False,'reason':'No passage engagement established: quotation/repost, inherited text, signature, unrelated conversation, or unresolved local relationship'});continue
  body=r['body'];matches=[m for m in r['matches'] if m['status']=='included']
  mask=bytearray(len(body))
  for m in matches:mask[m['start']:m['end']]=b'\1'*(m['end']-m['start'])
  toks=token_spans(body);vals=[t[0] for t in toks]
  for i in range(len(vals)-7):
   if tuple(vals[i:i+8]) in grams:
    u,v=toks[i][1],toks[i+7][2];mask[u:v]=b'\1'*(v-u)
  lines=[];off=0;footer=False
  footer_start=len(body)
  for fm in re.finditer(r'(?m)^--[ \t]*$',body):footer_start=min(footer_start,fm.start())
  for ln in body.splitlines(keepends=True):
   end=off+len(ln);quoted=bool(QDEPTH.match(ln));
   if not quoted and FOOTER.search(ln):footer=True
   # Only author-level prose is evidence of a new response. Prior writers'
   # quoted analysis remains context rather than being recounted as engagement.
   fresh=''.join(ch if not mask[j] else ' ' for j,ch in enumerate(body[off:end],off))
   plain=not quoted and not footer and bool(ln.strip())
   isprose=plain and meaningful(fresh)
   lines.append({'start':off,'end':end,'quoted':quoted,'blank':not ln.strip(),'prose':isprose,'fresh':fresh.strip(),'text':ln});off=end
  def li_at(pos):return next((i for i,l in enumerate(lines) if l['start']<=pos<l['end']),len(lines)-1)
  # Evaluate whole paragraphs, not individual wrapped lines. Short last lines
  # must not truncate an otherwise substantive reply halfway through a sentence.
  paragraphs=[];i=0
  generic=re.compile(r"(?is)^(?:here are (?:some of my favorite parts|two good paragraphs)|(?:from|the motives of scientists|the power process|the nature of freedom|how some people adjust|the psychology of modern leftism|the new luddite challenge|industrial society and its future)\s*$|(?:--)?\s*(?:the )?unabomber manifesto|(?:the famous )?unabomber said it best|(?:TK|FC|Kaczynski|Ted Kaczynski|Theodore Kaczynski).{0,35}(?:writes|wrote|says|said|sez)[:.\s]*$|relevent quotes about this|.*@[^\s]+\s*$|.*wrote in message.*$|news:|to:|--the declaration|industrial society and its future,? by)")
  while i<len(lines):
   if lines[i]['quoted'] or lines[i]['blank']:i+=1;continue
   a=i;j=i+1
   while j<len(lines) and not lines[j]['quoted'] and not lines[j]['blank']:j+=1
   u,v=lines[a]['start'],lines[j-1]['end'];raw=body[u:v]
   fresh=''.join(ch if not mask[k] else ' ' for k,ch in enumerate(raw,u))
   total=len(words(raw));nw=len(words(fresh));footer=bool(FOOTER.search(raw)) or bool(re.search(r'(?i)^\s*(?:--?\s*)?(?:industrial society and its future|the unabomber manifesto|Outcast! writing|THE THREE FACES OF THEODORE|Ross quoted from the manifesto|\(re:)',fresh.strip()))
   valid=(not footer and meaningful(fresh) and not generic.search(fresh.strip()) and not(nw<20 and nw<.4*max(1,total)))
   paragraphs.append({'start':u,'end':v,'a':a,'b':j-1,'valid':valid,'fresh':fresh})
   i=j
  regions=[]
  for z in paragraphs:
   if not z['valid']:continue
   if regions:
    prev=regions[-1];between=lines[prev[3]+1:z['a']]
    # A quotation (including an unmarked canonical block) ends a prose region.
    intervening=[p for p in paragraphs if p['start']>=prev[1] and p['end']<=z['start'] and not p['valid'] and sum(mask[p['start']:p['end']])>.35*(p['end']-p['start'])]
    if not any(l['quoted'] for l in between) and not intervening:
     regions[-1]=(prev[0],min(z['end'],footer_start),prev[2],z['b']);continue
   if z['start']<footer_start:regions.append((z['start'],min(z['end'],footer_start),z['a'],z['b']))
  groups={}
  for m in matches:
   if m.get('location')=='signature':continue
   li=li_at(m['start']);endli=li_at(max(m['start'],m['end']-1))
   # At quote depth >=1, walk through the complete inherited block so a
   # current writer's depth-zero response is not cut off prematurely.
   a=li;b=endli
   if lines[li]['quoted']:
    while a>0 and (lines[a-1]['quoted'] or lines[a-1]['blank']):a-=1
    while b+1<len(lines) and (lines[b+1]['quoted'] or lines[b+1]['blank']):b+=1
   nearby=[]
   for reg in regions:
    u,v,rl,rr=reg
    if u<=m['end'] and v>=m['start']:nearby.append(reg);continue
    # The immediate preceding or following prose region may introduce or
    # answer this quotation; another quoted exchange is a hard boundary.
    if rr<a:
     between=lines[rr+1:a]
    elif rl>b:between=lines[b+1:rl]
    else:between=[]
    if (rr<a or rl>b) and any(l['quoted'] or l['prose'] for l in between):continue
    if abs(u-m['end'])>12000 and abs(v-m['start'])>12000:continue
    nearby.append(reg)
   if not nearby:continue
   n=m['paragraph'] if m['kind']=='paragraph' else next((p['n'] for p in data['paragraphs'] if '['+str(m['paragraph'])+']' in p['text']),None)
   # Match the original import's parent assignment for original footnotes.
   if m['kind']!='paragraph':
    n=next((a['paras'][0] for a in original if a['postId']==r['id'] and m['start']>=a['excerptStart'] and m['end']<=a['excerptEnd']),None)
   if not n or not 1<=n<=232:continue
   key=tuple((z[0],z[1]) for z in nearby)
   g=groups.setdefault(key,{'ranges':key,'matches':[],'paras':set()});g['matches'].append(m);g['paras'].add(n)
  selected_groups=[]
  for g in sorted(groups.values(),key=lambda g:min(x['start'] for x in g['matches'])):
   response='\n'.join(body[u:v] for u,v in g['ranges']).strip()
   if re.fullmatch(r'(?is)[\s\W]*(?:[A-Za-z]+\s+)?(?:the )?unabomber manifesto.*',response):continue
   if response.startswith(('Outcast! writing','(see alt.fan.unabomber)','(re:')):continue
   if ri in [118,229,381] and len(words(response))<16 and re.search(r'(?i)(?:jumping to|writes about|consider paragraph)',response):continue
   if ri==127 and len(words(response))<15:continue
   if ri==162 and 'Having rather lucid' in response and len(words(response))<20:continue
   if ri==537 and len(words(response))<16:continue
   selected_groups.append(g)
  for gi,g in enumerate(selected_groups):
   parts=[]
   for m in g['matches']:parts.append({'start':m['start'],'end':m['end'],'role':'Quoted passage'})
   for u,v in g['ranges']:parts.append({'start':u,'end':v,'role':'Response'})
   # Merge overlapping spans of the same role; an inline quotation remains
   # part of its containing response rather than being repeated twice.
   responses=[p for p in parts if p['role']=='Response']
   parts=[p for p in parts if p['role']=='Response' or not any(z['start']<=p['start'] and z['end']>=p['end'] for z in responses)]
   merged=[]
   for p in sorted(parts,key=lambda p:(p['start'],p['end'])):
    if merged and p['role']==merged[-1]['role'] and p['start']<=merged[-1]['end']:merged[-1]['end']=max(merged[-1]['end'],p['end'])
    else:merged.append(dict(p))
   aid='usenet-'+r['id']+'-engagement-'+str(gi+1)
   entry={'id':aid,'source':'usenet-'+r['id'],'postId':r['id'],'paras':sorted(g['paras']),'title':r['subject'],'kind':'Usenet passage engagement','locator':'Message-ID: '+r['message_id']+'; reviewed local exchange '+str(gi+1),'category':'quotation_in_post','inheritedOnly':False,'excerptStart':min(p['start'] for p in merged),'excerptEnd':max(p['end'] for p in merged),'excerptNumber':gi+1,'notes':[],'engagementParts':merged}
   ann.append(entry)
   novel='\n'.join(body[u:v] for u,v in g['ranges']);review.append({'id':aid,'recordIndex':ri,'paras':entry['paras'],'response':novel})
  audit.append({'id':r['id'],'included':bool(selected_groups),'reason':'Reviewed content-related interpretation, application, criticism, or brief response' if selected_groups else 'No current-writer response could be separated from quoted text'})
 data['annotations']=[a for a in data['annotations'] if not a['source'].startswith('usenet-')]+ann
 used={a['source'] for a in ann};data['sources']=[s for s in data['sources'] if s.get('type')!='Usenet' or s['id'] in used]
 for source in data['sources']:
  if source.get('type')=='Usenet':
   source['category']='passage_engagement'
   source['provenance']+=' Selected for engagement with a quoted passage; quoted context and response are shown as separate exact excerpts.'
 ids={a['id'] for a in data['annotations']};pmap={p['n']:p for p in data['paragraphs']}
 for p in pmap.values():
  p['sources']=[s for s in p.get('sources',[]) if not s.startswith('usenet-')]
  p['anchors']=[dict(a,annotationIds=[i for i in a['annotationIds'] if i in ids]) for a in p.get('anchors',[]) if any(i in ids for i in a['annotationIds'])]
 for a in ann:
  r=next(r for r in records if r['id']==a['postId'])
  for n in a['paras']:
   p=pmap[n];rs=[]
   for m in r['matches']:
    if m['paragraph']==n and any(z['start']<=m['start'] and z['end']>=m['end'] for z in a['engagementParts']):
     ran=anchor_range(p['text'],m['quote'])
     if ran:rs.append(ran)
   if not rs:rs=[(0,token_spans(p['text'])[min(7,len(token_spans(p['text']))-1)][2])]
   for start,end in rs:p['anchors'].append({'start':start,'end':end,'annotationIds':[a['id']]})
   if a['source'] not in p['sources']:p['sources'].append(a['source'])
 for p in pmap.values():
  merged=[]
  for a in sorted(p['anchors'],key=lambda a:(a['start'],a['end'])):
   if merged and a['start']<merged[-1]['end']:
    merged[-1]['end']=max(merged[-1]['end'],a['end']);merged[-1]['annotationIds']=sorted(set(merged[-1]['annotationIds'])|set(a['annotationIds']))
   else:merged.append(dict(a))
  for i,a in enumerate(merged):a.update(id='a'+str(i),text=p['text'][a['start']:a['end']])
  p['anchors']=merged
 stats={'originalPosts':len(records),'retainedPosts':len(used),'removedPosts':len(records)-len(used),'originalAnnotations':len(original),'retainedAnnotations':len(ann),'removedAnnotations':len(original)-len(ann),'method':'Qualitative source selection plus structural selection of current-writer prose adjacent to quoted passages. Standalone reposts, signature-only quotations and unrelated exchanges excluded. Original raw messages preserved.'}
 data['usenetEngagementReview']=stats
 (DIST/'edition-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(DIST/'edition-data.js').write_text('const EDITION = '+json.dumps(data,ensure_ascii=False)+';')
 (ROOT/'source/usenet-review/decisions.json').write_text(json.dumps(audit,indent=2));(ROOT/'source/usenet-review/selected-exchanges.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
 (DIST/'usenet-engagement-review.md').write_text('# Usenet passage-engagement review\n\n'+json.dumps(stats,indent=2)+'\n\nBrief agreement, rejection and critical discussion can qualify. A matched or inherited quotation alone does not. Excerpts label the quoted passage separately from the current response and use exact source slices. This is one-reviewer qualitative selection assisted by structural rules; remaining ambiguous associations can be checked against the linked full posts. The original 723 message records and EML files remain preserved as archival sources.\n')
 print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
