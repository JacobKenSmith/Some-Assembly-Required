from pathlib import Path
import json
root=Path(__file__).resolve().parent
data=json.loads((root/'dist/edition-data.json').read_text());pilot=json.loads((root/'source/pilot-edition.json').read_text());posts=[json.loads(s) for s in (root/'source/usenet-posts.jsonl').read_text().splitlines()]
assert [p['n'] for p in data['paragraphs']]==list(range(1,233))
assert len(data['footnotes'])==36
assert data['annotations'][:len(pilot['annotations'])]==pilot['annotations']
assert data['sources'][:len(pilot['sources'])]==pilot['sources']
for old in pilot['paragraphs']:
 new=next(p for p in data['paragraphs'] if p['n']==old['n'])
 assert new['text']==old['text']
 if old['highlight']:assert new['highlight']==old['highlight']
for p in data['paragraphs']:
 assert not p['highlight'] or p['highlight'] in p['text'],p['n']
assert len([s for s in data['sources'] if s['type']=='Usenet'])==len(posts)==723
sids={s['id'] for s in data['sources']}
assert {a['source'] for a in data['annotations'] if a['source'].startswith('usenet-')}=={s['id'] for s in data['sources'] if s['type']=='Usenet'}
annotation_ids={a['id'] for a in data['annotations']}
assert len(annotation_ids)==len(data['annotations'])
by_post={p['id']:p for p in posts}
for a in data['annotations']:
 if 'excerptStart' in a:
  body=by_post[a['postId']]['body']
  assert 0<=a['excerptStart']<a['excerptEnd']<=len(body)
for p in data['paragraphs']:
 previous=0
 for anchor in p['anchors']:
  assert previous<=anchor['start']<anchor['end']<=len(p['text'])
  assert p['text'][anchor['start']:anchor['end']]==anchor['text']
  assert all(i in annotation_ids for i in anchor['annotationIds'])
  previous=anchor['end']
for a in data['annotations']:
 assert a['source'] in sids and all(1<=n<=232 for n in a['paras'])
for s in data['sources']:
 if s['type']=='Usenet':
  assert (root/'dist'/s['url']).is_file()
  assert (root/'dist'/s['postData']).is_file()
for p in posts:
 payload=json.loads((root/'dist/usenet/posts'/(p['id']+'.json')).read_text())
 assert payload['body']==p['body']
 assert (root/'dist/usenet/posts'/(p['id']+'.eml')).is_file()
 assert ('usenet-'+p['id']) in sids
print('Verified: all 723 posts and original-message files; 232 paragraphs; 36 notes; all prior sources/annotations preserved; all anchors valid.')
