"""Preserve verbatim quote/reply blocks as separately addressable reception notes."""
import re

WORD=re.compile(r"[A-Za-z]+(?:(?:['’][A-Za-z]+)|(?:[-\u00ad][ \t]*\n[ \t>]*[A-Za-z]+))*")
def token_spans(text):
    return [(re.sub(r'[-\u00ad][ \t]*\n[ \t>]*','',m[0]).lower().replace('’',"'").replace("'",''),m.start(),m.end()) for m in WORD.finditer(text)]

def anchor_range(text,quote):
    source=token_spans(text);target=token_spans(quote)
    vals=[t[0] for t in source];qs=[t[0] for t in target]
    for length in (12,10,8):
        if len(qs)<length:continue
        lookup={tuple(vals[i:i+length]):i for i in range(len(vals)-length+1)}
        for i in range(len(qs)-length+1):
            j=lookup.get(tuple(qs[i:i+length]))
            if j is not None:return source[j][1],source[j+length-1][2]
    return None

def lines_of(body):
    out=[];pos=0
    for line in body.splitlines(keepends=True):
        p=re.match(r'^\s*((?:[>|:]\s*)+)',line)
        depth=len(re.findall(r'[>|:]',p[1])) if p else 0
        out.append(dict(start=pos,end=pos+len(line),depth=depth,blank=not line.strip(),text=line))
        pos+=len(line)
    return out

def split_engagements(record,parent_para):
    body=record['body'];matches=[m for m in record['matches'] if m['status']=='included'];lines=lines_of(body)
    if not lines:return []
    def line_at(offset):
        # Archives are small enough that this transparent lookup stays inexpensive.
        return next((i for i,l in enumerate(lines) if l['start']<=offset<l['end']),len(lines)-1)
    groups={}
    for mi,m in enumerate(matches):
        para=parent_para(m)
        if not para:continue
        li=line_at(m['start']);last=line_at(max(m['start'],m['end']-1));depth=lines[li]['depth']
        if record['category']=='extended_reproduction':
            # A reproduction has no inferred reply. Retain only this numbered source unit.
            start,end=m['start'],m['end'];key=('reproduction',m['unit'],mi)
        elif m.get('location')=='signature':
            start,end=lines[li]['start'],lines[last]['end'];key=('signature',start,end)
        elif depth:
            first=li
            while first>0 and (lines[first-1]['depth']>=depth or lines[first-1]['blank']):first-=1
            while first<li and lines[first]['blank']:first+=1
            # Finish the quote at the same nesting level, then keep the immediate reply.
            j=last+1
            while j<len(lines) and (lines[j]['depth']>=depth or lines[j]['blank']):j+=1
            while j<len(lines):
                l=lines[j]
                if not l['blank'] and (l['depth']>=depth or l['depth']<depth-1 or re.match(r'^--\s*$',l['text'])):break
                j+=1
            start=lines[first]['start'];end=lines[j]['start'] if j<len(lines) else len(body)
            key=('quoted',start,end)
        else:
            # Inline/unmarked citations: preserve their containing prose and following reply,
            # stopping at the next explicit quotation or separately matched passage.
            start=lines[li]['start'];end=len(body)
            for l in lines[last+1:]:
                if l['depth'] or re.match(r'^--\s*$',l['text']):end=l['start'];break
            for other in matches[mi+1:]:
                if other['start']>=m['end']:
                    between=body[m['end']:other['start']]
                    if re.search(r'[A-Za-z]',between):end=min(end,lines[line_at(other['start'])]['start']);break
            end=max(end,m['end']);key=('inline',start,end)
        if key not in groups:groups[key]=dict(start=start,end=end,matches=[],paras=set(),kind=key[0])
        g=groups[key];g['start']=min(g['start'],start);g['end']=max(g['end'],end);g['matches'].append(m);g['paras'].add(para)
    result=[]
    for g in sorted(groups.values(),key=lambda x:(x['start'],x['end'])):
        # Trim whitespace only at boundaries; every displayed character remains in the post.
        a,b=g['start'],g['end']
        while a<b and body[a].isspace():a+=1
        while b>a and body[b-1].isspace():b-=1
        g.update(start=a,end=b,paras=sorted(g['paras']))
        if b>a:result.append(g)
    return result

def make_anchors(paragraph,annotations,records_by_id):
    text=paragraph['text'];candidates=[]
    legacy=[a['id'] for a in annotations if not a['source'].startswith('usenet-') and paragraph['n'] in a['paras']]
    if paragraph.get('highlight') and legacy:
        start=text.find(paragraph['highlight'])
        if start>=0:candidates.append(dict(start=start,end=start+len(paragraph['highlight']),ids=set(legacy)))
    for a in annotations:
        if not a['source'].startswith('usenet-') or paragraph['n'] not in a['paras']:continue
        record=records_by_id[a['postId']];matched=[]
        for m in record['matches']:
            if m['status']!='included' or m['start']<a['excerptStart'] or m['end']>a['excerptEnd']:continue
            if m['kind']=='paragraph' and m['paragraph']==paragraph['n']:matched.append(m)
        ranges=[anchor_range(text,m['quote']) for m in matched];ranges=[r for r in ranges if r]
        if not ranges:
            # A quoted footnote is explicitly attached to its parent paragraph.
            if paragraph.get('highlight'):
                start=text.find(paragraph['highlight']);ranges=[(start,start+len(paragraph['highlight']))]
            else:
                ws=token_spans(text);ranges=[(0,ws[min(7,len(ws)-1)][2])] if ws else []
        for start,end in ranges:candidates.append(dict(start=start,end=end,ids={a['id']}))
    merged=[]
    for c in sorted(candidates,key=lambda c:(c['start'],c['end'])):
        if merged and c['start']<merged[-1]['end']:
            merged[-1]['end']=max(merged[-1]['end'],c['end']);merged[-1]['ids'].update(c['ids'])
        else:merged.append(c)
    return [dict(id='a'+str(i),start=c['start'],end=c['end'],text=text[c['start']:c['end']],annotationIds=sorted(c['ids'])) for i,c in enumerate(merged)]
