#!/usr/bin/env python3
"""Populate the established edition from the preserved, source-matched Usenet archive."""
from pathlib import Path
from html.parser import HTMLParser
import collections, datetime as dt, email.utils, html, json, re, sys
from passage_notes import split_engagements, make_anchors
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source';DIST=ROOT/'dist'

class BaseParser(HTMLParser):
    def __init__(self):
        super().__init__();self.intext=False;self.depth=0;self.block=None;self.buf=[];self.blocks=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id')=='htmltextbody':self.intext=True;self.depth=1;return
        if self.intext:
            if tag=='div':self.depth+=1
            if tag in ['p','h2','h3','h4']:
                self.block=tag;self.buf=[]
    def handle_data(self,data):
        if self.intext and self.block:self.buf.append(data)
    def handle_endtag(self,tag):
        if self.intext and tag==self.block:
            self.blocks.append((tag,' '.join(''.join(self.buf).split())));self.block=None
        if self.intext and tag=='div':
            self.depth-=1
            if self.depth<=0:self.intext=False

def words(s):return re.findall(r"[a-z]+(?:['’][a-z]+)?",s.lower().replace('’',"'"))
def anchor(text,phrase):
    if phrase in text:return phrase
    # Anchor the same words across harmless case, punctuation and apostrophe differences.
    target=words(phrase);spans=list(re.finditer(r"[A-Za-z]+(?:['’][A-Za-z]+)?",text))
    values=[m[0].lower().replace('’',"'") for m in spans]
    for i in range(len(values)-len(target)+1):
        if values[i:i+len(target)]==target:return text[spans[i].start():spans[i+len(target)-1].end()]
    return ''

def main():
    p=BaseParser();p.feed((SOURCE/'base-text.html').read_text())
    paras={};notes={};sections=[];current=None;section=None;innotes=False
    for tag,text in p.blocks:
        if tag.startswith('h'):
            if text:section=text
            continue
        m=re.match(r'^(\d{1,3})\.\s*(.*)',text)
        note=re.match(r'^\[(\d{1,2})\]\s*(.*)',text)
        if note:notes[note[1]]=note[2];innotes=True;current=None;continue
        if innotes:
            if notes:notes[next(reversed(notes))]+=' '+text
            continue
        if m and 1<=int(m[1])<=232:
            n=int(m[1]);current=n
            if section and (not sections or sections[-1]['title']!=section):sections.append(dict(title=section,start=n))
            paras[n]=dict(n=n,text=m[2],section=section or 'Introduction',highlight='',sources=[])
        elif current and text:paras[current]['text']+=' '+text
    if sorted(paras)!=list(range(1,233)):raise ValueError(f'Base text incomplete: {len(paras)} numbered paragraphs')
    if len(notes)!=36:raise ValueError(f'Base notes incomplete: {len(notes)}')
    for i,s in enumerate(sections):s['end']=sections[i+1]['start']-1 if i+1<len(sections) else 232
    pilot=json.loads((SOURCE/'pilot-edition.json').read_text())
    for old in pilot['paragraphs']:
        # Preserve the exact established Strategy text and its active phrases.
        paras[old['n']]['text']=old['text']
        paras[old['n']]['highlight']=old['highlight']
    note_parents={int(note):n for n,p in paras.items() for note in re.findall(r'\[(\d+)\]',p['text'])}
    if len(note_parents)!=36:raise ValueError('Incomplete footnote-to-paragraph map')
    sources=pilot['sources'][:];annotations=pilot['annotations'][:]
    records=[json.loads(x) for x in (SOURCE/'usenet-posts.jsonl').read_text().splitlines()]
    archive_root=Path(sys.argv[1]) if len(sys.argv)>1 else None
    postsdir=DIST/'usenet'/'posts';postsdir.mkdir(parents=True,exist_ok=True)
    html_escape=html.escape
    def parent_para(match):
        if match['kind']=='paragraph':return match['paragraph']
        return note_parents.get(match['paragraph'])
    refs=json.loads((SOURCE/'usenet-extraction-summary.json').read_text())
    for r in records:
        sid='usenet-'+r['id'];ms=[m for m in r['matches'] if m['status']=='included']
        targets=sorted({parent_para(m) for m in ms if parent_para(m) in paras})
        if not targets:raise ValueError('Unmapped post: '+r['id'])
        name,address=email.utils.parseaddr(r['author']);date=dt.date.fromisoformat(r['date'][:10])
        displaydate=f'{date.day} {date.strftime("%B %Y")}'
        sources.append(dict(id=sid,name=name or address or r['author'],short=name or address or r['author'],year=date.year,
            date=displaydate,dateISO=r['date'],rawDate=r['raw_date'],outlet='alt.fan.unabomber',type='Usenet',
            title=r['subject'],url=f'usenet/posts/{r["id"]}.html',postData=f'usenet/posts/{r["id"]}.json',
            address=r['author'],messageId=r['message_id'],category=r['category'],newsgroups=r['newsgroups'],
            provenance='Original Usenet post preserved in the supplied mbox. Quotation matched against two archived manifesto reposts; paragraph numbers retained. A carried-forward quotation is not attributed as agreement by this poster.'))
        segments=split_engagements(r,parent_para)
        for i,segment in enumerate(segments):
            annotations.append(dict(id=sid+'-excerpt-'+str(i+1),source=sid,postId=r['id'],
                paras=segment['paras'],title=r['subject'],kind='Usenet passage',
                locator='Message-ID: '+r['message_id']+'; passage '+str(i+1),
                category=r['category'],inheritedOnly=all(m['location']=='inherited_quote' for m in segment['matches']),
                excerptStart=segment['start'],excerptEnd=segment['end'],excerptNumber=i+1,
                notes=sorted({m['paragraph'] for m in segment['matches'] if m['kind']=='note'})))
        # Context files retain each complete body; note bodies are fetched only when opened.
        matches=[dict(start=m['start'],end=m['end'],paragraph=parent_para(m),unit=m['unit'],location=m['location']) for m in ms]
        payload=dict(id=r['id'],body=r['body'],matches=matches,headers=r['headers'],category=r['category'])
        (postsdir/(r['id']+'.json')).write_text(json.dumps(payload,ensure_ascii=False),encoding='utf8')
        header='\n'.join(k+': '+v for k,v in r['headers'].items() if v)
        bodyparts=[];cursor=0
        for m in ms:
            bodyparts.append(html_escape(r['body'][cursor:m['start']]))
            bodyparts.append(f'<mark title="{html_escape(m["unit"])}">'+html_escape(r['body'][m['start']:m['end']])+'</mark>');cursor=m['end']
        bodyparts.append(html_escape(r['body'][cursor:]))
        links=' · '.join(f'<a href="../../index.html#p{n}/{sid}">§{n}</a>' for n in targets)
        original_link=''
        if archive_root:
            eml=(archive_root/r['original_eml']).read_bytes();(postsdir/(r['id']+'.eml')).write_bytes(eml)
        if archive_root or (postsdir/(r['id']+'.eml')).exists():
            original_link=f'<p><a href="{r["id"]}.eml" download>Download original message (.eml)</a></p>'
        page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html_escape(r['subject'])+'</title><style>body{max-width:850px;margin:35px auto;padding:0 24px;background:#fcfcfa;color:#22211f;font:17px/1.6 Georgia,serif}h1{font-size:26px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.7 monospace}a{color:#435238}mark{background:#e6ebdf}header{font:13px/1.6 system-ui,sans-serif;border-bottom:1px solid #ccc;padding-bottom:15px}</style><a href="../../index.html#p'+str(targets[0])+'/'+sid+'">← Return to the annotated text</a><h1>'+html_escape(r['subject'])+'</h1><header><pre>'+html_escape(header)+'</pre><p>Matched passages: '+links+'</p>'+original_link+'</header><pre>'+''.join(bodyparts)+'</pre></html>'
        (postsdir/(r['id']+'.html')).write_text(page,encoding='utf8')
    source_map={s['id']:s for s in sources}
    for n,paragraph in paras.items():
        relevant=[a for a in annotations if n in a['paras']]
        paragraph['sources']=list(dict.fromkeys(a['source'] for a in relevant))
        if paragraph['highlight']:continue
        # Select an actual shared span from a smaller quoted post for the paragraph anchor.
        candidates=[]
        for r in records:
            if r['category']=='extended_reproduction':continue
            for m in r['matches']:
                if m['status']=='included' and m['kind']=='paragraph' and m['paragraph']==n:
                    quoted=re.sub(r'(?m)^\s*[>|]+\s*','',m['quote'])
                    ws=list(re.finditer(r"[A-Za-z]+(?:['’][A-Za-z]+)?",quoted))
                    if len(ws)>12:quoted=quoted[:ws[11].end()]
                    hit=anchor(paragraph['text'],quoted)
                    if hit:candidates.append(hit)
        if candidates:paragraph['highlight']=collections.Counter(candidates).most_common(1)[0][0]
        elif relevant:
            # An original note or a reproduction still belongs to its numbered paragraph.
            ws=list(re.finditer(r"[A-Za-z]+(?:['’][A-Za-z]+)?",paragraph['text']))
            paragraph['highlight']=paragraph['text'][:ws[min(11,len(ws)-1)].end()] if ws else ''
    records_by_id={r['id']:r for r in records}
    for paragraph in paras.values():paragraph['anchors']=make_anchors(paragraph,annotations,records_by_id)
    stats=dict(posts=len(records),shorterPosts=refs['quotation_posts'],extendedReproductions=refs['extended_reproductions'],
        usenetAnnotations=sum(a['source'].startswith('usenet-') for a in annotations),periodicalAnnotations=len(pilot['annotations']),
        quotedDiscussionParagraphs=len({n for a in annotations if a.get('category')=='quotation_in_post' for n in a['paras']}))
    data=dict(paragraphs=list(paras.values()),sources=sources,annotations=annotations,footnotes=notes,sections=sections,
              context=pilot['context'],baseUrl=pilot['baseUrl'],importStats=stats)
    (DIST/'edition-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    (DIST/'edition-data.js').write_text('const EDITION = '+json.dumps(data,ensure_ascii=False)+';',encoding='utf8')
    audit=('# Usenet population of the annotated edition\n\n'+json.dumps(stats,indent=2)+'\n\n'
      'All 723 selected raw post records are represented, without deduplication. Full context pages preserve decoded bodies and link original EML bytes. '
      'The 10 ambiguous overlap candidates remain in the extraction archive and are not imported as verified paragraph notes. '
      'Default reception notes omit extended reproductions; the reader can include them or select them separately. '
      'The original 16 annotations and 6 non-Usenet sources remain unchanged. '
      'The reading text uses the same Anarchist Library version as the pilot, expanded to all 232 paragraphs and 36 original notes. '
      'The pilot’s exact Strategy paragraph text is retained. Text matching was performed against archived reposts, so edition variants can differ. '
      'Footnote quotations attach to their explicitly named parent paragraph and retain their note number. '
      'Bubbles show verbatim quote/reply blocks, with separate notes for distinct exchanges in a post. Full posts remain on context pages. Nested quotes use their immediate reply level; continuous prose is segmented conservatively. '
      'Quoted replies and signatures are labeled; inclusion does not establish endorsement.\n')
    (DIST/'usenet-import-audit.md').write_text(audit,encoding='utf8')
    print(json.dumps(stats));print('Sections:',len(sections),'Footnotes:',len(notes))

if __name__=='__main__':main()
