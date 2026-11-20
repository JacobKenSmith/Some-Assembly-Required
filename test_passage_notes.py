import unittest
from passage_notes import split_engagements,make_anchors

def record(body,specs,category='quotation_in_post'):
    matches=[];pos=0
    for phrase,para in specs:
        start=body.index(phrase,pos);end=start+len(phrase);pos=end
        matches.append(dict(start=start,end=end,paragraph=para,unit='p'+str(para),kind='paragraph',quote=phrase,location='inherited_quote',status='included'))
    return dict(body=body,matches=matches,category=category)

class PassageNotesTests(unittest.TestCase):
    def test_two_distinct_quotes_get_only_their_own_replies(self):
        body='> A quotation from the first paragraph.\n\nThe reply about the first quotation.\n\n> A quotation from the second paragraph.\n\nThe reply about the second quotation.'
        r=record(body,[('A quotation from the first paragraph.',1),('A quotation from the second paragraph.',2)])
        groups=split_engagements(r,lambda m:m['paragraph'])
        self.assertEqual(len(groups),2)
        one=body[groups[0]['start']:groups[0]['end']];two=body[groups[1]['start']:groups[1]['end']]
        self.assertIn('reply about the first',one);self.assertNotIn('second',one)
        self.assertIn('reply about the second',two);self.assertNotIn('first',two)
    def test_unrelated_nonmanifesto_quote_also_ends_the_excerpt(self):
        body='> A manifesto quotation about political movements.\n\nThis reply discusses Earth First.\n\n> A different writer discusses Situationists.\n\nThis reply discusses UNAPACK.'
        r=record(body,[('A manifesto quotation about political movements.',214)])
        group=split_engagements(r,lambda m:m['paragraph'])[0]
        excerpt=body[group['start']:group['end']]
        self.assertIn('Earth First',excerpt);self.assertNotIn('UNAPACK',excerpt);self.assertNotIn('Situationists',excerpt)
    def test_separate_exchanges_in_same_manifesto_paragraph_stay_separate(self):
        body='> A first quote from a single paragraph.\nReply one.\n> A second quote from that same paragraph.\nReply two.'
        r=record(body,[('A first quote from a single paragraph.',1),('A second quote from that same paragraph.',1)])
        gs=split_engagements(r,lambda m:m['paragraph']);self.assertEqual(len(gs),2)
        self.assertEqual(gs[0]['paras'],[1]);self.assertEqual(gs[1]['paras'],[1])
    def test_shared_reply_is_not_falsely_divided(self):
        body='> First paragraph quoted.\n> Second paragraph quoted.\n\nA reply addressing both together.'
        r=record(body,[('First paragraph quoted.',1),('Second paragraph quoted.',2)])
        gs=split_engagements(r,lambda m:m['paragraph']);self.assertEqual(len(gs),1);self.assertEqual(gs[0]['paras'],[1,2])
    def test_nested_quote_keeps_its_immediate_reply(self):
        body='>> Nested manifesto quotation.\n> Its immediate reply.\n\nCurrent poster changes topic.'
        r=record(body,[('Nested manifesto quotation.',1)])
        g=split_engagements(r,lambda m:m['paragraph'])[0]
        excerpt=body[g['start']:g['end']]
        self.assertIn('immediate reply',excerpt);self.assertNotIn('changes topic',excerpt)
    def test_separate_quote_anchors_point_to_separate_annotations(self):
        body='First distinct passage with enough words to anchor the first annotation. Second distinct passage with enough words to anchor the other annotation.'
        r=record(body,[('First distinct passage with enough words to anchor the first annotation.',1),('Second distinct passage with enough words to anchor the other annotation.',1)])
        anns=[dict(id='x'+str(i),source='usenet-post',postId='post',paras=[1],excerptStart=m['start'],excerptEnd=m['end']) for i,m in enumerate(r['matches'])]
        anchors=make_anchors(dict(n=1,text=body,highlight=''),anns,{'post':r})
        self.assertEqual(len(anchors),2)
        self.assertEqual(anchors[0]['annotationIds'],['x0']);self.assertEqual(anchors[1]['annotationIds'],['x1'])

if __name__=='__main__':unittest.main()
