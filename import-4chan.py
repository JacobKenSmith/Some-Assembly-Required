"""Add curated 4chan quote responses without changing prior edition content."""
from pathlib import Path
from html import escape
import json,re,collections,shutil
from passage_notes import token_spans,anchor_range,split_engagements
ROOT=Path(__file__).resolve().parent;DIST=ROOT/'dist'
def span_for(body,quote):
 a=token_spans(body);b=token_spans(quote);vals=[v[0] for v in a];needle=[v[0] for v in b]
 if not needle:return None
 for i in range(len(vals)-len(needle)+1):
  if vals[i:i+len(needle)]==needle:return a[i][1],a[i+len(needle)-1][2]
 return None

def reply_excerpt(row,parentids):
 """Retain a local reply block when a post answers several separate post IDs."""
 body=row['Comment'];lines=body.splitlines(keepends=True);positions=[];offset=0
 for i,line in enumerate(lines):
  m=re.fullmatch(r'\s*>>([0-9]+)\s*',line)
  if m:positions.append((offset,m[1],i))
  offset+=len(line)
 if not positions:return body
 # Consecutive reply references share their following response rather than being
 # arbitrarily split into empty notes. A new block after prose starts a new exchange.
 groups=[]
 for off,pid,li in positions:
  if groups and not ''.join(lines[groups[-1]['last_line']+1:li]).strip():
   groups[-1]['ids'].append(pid);groups[-1]['last_line']=li
  else:groups.append({'start':off,'ids':[pid],'last_line':li})
 relevant=[g for g in groups if any(p in parentids for p in g['ids'])]
 if len(relevant)!=1:return body
 g=relevant[0];j=groups.index(g);end=groups[j+1]['start'] if j+1<len(groups) else len(body)
 return body[g['start']:end].strip()

def html_post(row):
 pid=row['Post ID'];contexts=json.loads(row['Reply-context JSON'] or '[]')
 ctx=''.join(f'<section><h2>Linked post <a href="{escape(c["post_url"])}">{escape(c["post_id"])}</a></h2><pre>{escape(c["parent_post_text"])}</pre></section>' for c in contexts)
 return '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Post '+pid+'</title><style>body{max-width:850px;margin:3rem auto;padding:0 24px;background:#fcfcfa;color:#222;font:18px/1.6 Georgia}pre{font:inherit;white-space:pre-wrap;overflow-wrap:anywhere}a{color:#435238}h1,h2{font-weight:400}small{font:14px/1.5 system-ui}</style>'+f'<p><a href="../../index.html">Some Assembly Required</a></p><h1>Post {pid}</h1><small>{escape(row["Source date/time"])} · {escape(row["Series"])} · {escape(row["Response category"])}</small><p><a href="{escape(row["Source post URL"])}">Original archived post and thread</a> · <a href="{pid}.json">Preserved post data</a></p><pre>{escape(row["Comment"])}</pre><p>{escape(row["Context note"])}</p>'+ctx

def main():
 data=json.loads((DIST/'edition-data.json').read_text());rows=json.loads((ROOT/'source/tkg-responses.json').read_text())
 old_sources=[s for s in data['sources'] if s.get('type')!='4chan'];old_ann=[a for a in data['annotations'] if not a['id'].startswith('4chan-')]
 data['sources']=old_sources[:];data['annotations']=old_ann[:];data['additionalResponses']=[]
 pmap={p['n']:p for p in data['paragraphs']}
 for p in pmap.values():
  for a in p.get('anchors',[]):a['annotationIds']=[x for x in a['annotationIds'] if not x.startswith('4chan-')]
  p['anchors']=[a for a in p.get('anchors',[]) if a['annotationIds']]
  p['sources']=[s for s in p.get('sources',[]) if not s.startswith('4chan-')]
 records=DIST/'4chan/posts';records.mkdir(parents=True,exist_ok=True)
 for row in rows:
  pid=row['Post ID'];sid='4chan-'+pid;targets=json.loads(row['Target quoted passages JSON']);nums=[int(v) for v in row['Manifesto paragraph numbers'].split('; ') if v]
  source={'id':sid,'name':(row['Name'] or 'Anonymous')+' · '+pid,'short':'/pol/ '+pid,'year':int(row['Source date/time'][:4]),'date':row['Source date/time'][:10],'outlet':'4chan /pol/ · '+row['Series'],'type':'4chan','title':'Post '+pid,'url':'4chan/posts/'+pid+'.html','archiveUrl':row['Source post URL'],'color':'#806b42','provenance':'Preserved archive text. '+row['Response relationship']+'. '+row['Paragraph mapping basis']+'. '+row['Context note'],'category':'quote_response'}
  data['sources'].append(source)
  (records/(pid+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2));(records/(pid+'.html')).write_text(html_post(row))
  own=[m for m in targets if m['relation']=='Quotation in response post' and m['work']=='Industrial Society and Its Future']
  matched=[]
  for m in own:
   n=re.search(r'Paragraph (\d+)',m['locator']);span=span_for(row['Comment'],m['matched_post_excerpt'])
   if n and span:matched.append({'start':span[0],'end':span[1],'status':'included','kind':'paragraph','paragraph':int(n[1]),'unit':int(n[1]),'quote':row['Comment'][span[0]:span[1]]})
  groups=[]
  if matched:
   record={'body':row['Comment'],'matches':sorted(matched,key=lambda x:x['start']),'category':'quotation_in_post'}
   for gi,g in enumerate(split_engagements(record,lambda m:m['paragraph'])):
    # A leading interpretation introduces the first quote; preserve it rather
    # than silently reducing a critical/approving post to a quotation-only note.
    start=0 if gi==0 else g['start']
    groups.append({'paras':g['paras'],'excerpt':row['Comment'][start:g['end']],'quoteExcerpt':'','quotePostIds':[],'targetPassages':[m for m in own if int(re.search(r'Paragraph (\d+)',m['locator'])[1]) in g['paras']]})
  # For replies without their own matching quote, preserve quoted parent plus
  # the responding text. A shared reply stays attached to its shared passages.
  remaining=set(nums)-{n for g in groups for n in g['paras']}
  if remaining:
   par=[m for m in targets if m['relation']=='Quotation in linked parent' and m['work']=='Industrial Society and Its Future' and re.search(r'Paragraph (\d+)',m['locator']) and int(re.search(r'Paragraph (\d+)',m['locator'])[1]) in remaining]
   parentids=list(dict.fromkeys(m['context_post_id'] for m in par))
   quotes=list(dict.fromkeys(m['matched_post_excerpt'] for m in par))
   if 'Fourteen-words' in row['Response category'] and not quotes:quotes=[pmap[1]['text'].split('. ')[0]+'.']
   groups.append({'paras':sorted(remaining),'excerpt':reply_excerpt(row,parentids),'quoteExcerpt':'\n\n'.join(quotes),'quotePostIds':parentids,'targetPassages':par})
  for i,g in enumerate(groups):
   aid=sid+'-response-'+str(i+1)
   ann={'id':aid,'source':sid,'paras':g['paras'],'title':row['Response category'],'kind':row['Response category'],'body':'','locator':row['Paragraph mapping basis'],'excerpt':g['excerpt'],'quoteExcerpt':g['quoteExcerpt'],'quotePostIds':g['quotePostIds'],'postId':pid,'mappingNote':row['Context note'],'category':'quote_response'}
   data['annotations'].append(ann)
   for n in g['paras']:
    p=pmap[n];ranges=[anchor_range(p['text'],m['matched_post_excerpt']) for m in g['targetPassages']];ranges=[v for v in ranges if v]
    if not ranges:ranges=[(0,token_spans(p['text'])[min(7,len(token_spans(p['text']))-1)][2])]
    for start,end in ranges:p['anchors'].append({'id':'new','start':start,'end':end,'text':p['text'][start:end],'annotationIds':[aid]})
    if sid not in p['sources']:p['sources'].append(sid)
  # Other books and unmapped citations have a visibly separate location; do
  # not invent a numbered-manifesto anchor for a page from another work.
  if not nums:
   quote='\n\n'.join(dict.fromkeys(m.get('matched_post_excerpt','') for m in targets if m.get('matched_post_excerpt') and m['relation']=='Quotation in linked parent'))
   data['additionalResponses'].append({'id':sid,'source':sid,'work':row['Target works'] or 'Passage reference not resolved','kind':row['Response category'],'quoteExcerpt':quote,'excerpt':row['Comment'],'mappingNote':row['Context note']})
 for p in pmap.values():
  merged=[]
  for a in sorted(p['anchors'],key=lambda a:(a['start'],a['end'])):
   if merged and a['start']<merged[-1]['end']:
    merged[-1]['end']=max(merged[-1]['end'],a['end']);merged[-1]['annotationIds']=sorted(set(merged[-1]['annotationIds'])|set(a['annotationIds']))
   else:merged.append(dict(a))
  for i,a in enumerate(merged):a.update(id='a'+str(i),text=p['text'][a['start']:a['end']])
  p['anchors']=merged
 data['fourchanImportStats']={'posts':len(rows),'manifestoPosts':sum(bool(r['Manifesto paragraph numbers']) for r in rows),'manifestoAnnotations':sum(a['id'].startswith('4chan-') for a in data['annotations']),'otherOrUnresolvedPosts':len(data['additionalResponses']),'fourteenWordsPosts':sum('Fourteen-words' in r['Response category'] for r in rows),'categories':dict(collections.Counter(r['Response category'] for r in rows))}
 assert data['sources'][:len(old_sources)]==old_sources and data['annotations'][:len(old_ann)]==old_ann
 (DIST/'edition-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(DIST/'edition-data.js').write_text('const EDITION = '+json.dumps(data,ensure_ascii=False)+';',encoding='utf8')
 audit='# 4chan quote responses\n\n'+json.dumps(data['fourchanImportStats'],indent=2)+'\n\nSelected from the 777 passage-candidate records, with five additional fourteen-words posts recovered from the full saved corpus. One-reviewer qualitative categories separate brief reactions, dismissals, interpretation, critical disputes and quotation circulation. Quote-only continuations, empty/image-only replies, logistics and responses to unrelated accompanying text were excluded. No attached images were assessed. A reply link identifies a parent post; textual review supplies the inclusion decision. Numbered-manifesto anchors use matched wording or explicitly labeled poster-supplied citations. Other works and unresolved references are separate. Previous periodical and Usenet annotations are preserved. The source CSV retains original post text, parent context and coding.\n'
 (DIST/'4chan-import-audit.md').write_text(audit)
 print(json.dumps(data['fourchanImportStats'],indent=2))
if __name__=='__main__':main()
