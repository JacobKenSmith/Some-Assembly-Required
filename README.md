# Some Assembly Required — annotated manifesto

The text-first annotated reader lives in `dist/index.html`. The complete 232-paragraph text is the initial view. The section selector
jumps within that continuous text without hiding other sections. One thought bubble is active at a time;
notes appear below passages on narrow screens.

Usenet population: 723 preserved post records (606 smaller quotation posts,
117 extended reproductions). The reader now uses the engagement selection described below. Standalone
reproductions and unrelated quotations no longer appear among reception notes. Usenet notes show separately addressable verbatim quote/reply exchanges,
with matches highlighted. Different quoted passages within a post have distinct
annotations and passage anchors. A shared reply to consecutive quotations stays
together rather than being assigned arbitrarily. Context pages retain complete
posts, full headers, and links to original EML.
Quoted reply chains, signature quotations and repeated posts remain source evidence.
Their inclusion is not a stance classification. Ten ambiguous extraction candidates
remain outside the edition; see the separately saved extraction archive.

The prior pilot's 16 annotations and six sources remain unchanged. All Strategy
paragraph text and highlights are retained exactly. Other reading text and the
36 original notes use the same Anarchist Library transcription as that pilot.
The matching archive used two historical reposts; edition differences are documented.
Footnote quotes map to the paragraph carrying their footnote marker.

## Build and verify

No frontend build step or third-party Python dependency is required.
`source/pilot-edition.json` preserves the pre-import edition.
`source/base-text.html` preserves the fetched base transcription.
`source/usenet-posts.jsonl` and `source/usenet-extraction-summary.json` preserve
selected post content and extraction provenance.

```
python import-usenet.py /path/to/extracted/manifesto_quote_archive
python check-import.py
node --check dist/edition.js
```

The argument to the importer is optional if original EML files are already in
the checkout. It supplies `original_eml/` from the extracted research archive on
initial import. `dist/usenet-import-audit.md` records counts and provenance.

This is a static Site. Preserve `.openai/hosting.json` and its project identity.
The historical `build-edition.py` created the bounded Strategy pilot and depends
on its original research workspace; use `import-usenet.py` for the current edition.

## Quote-specific excerpts

`passage_notes.py` segments posts at explicit quotation/reply boundaries, including
nesting depth. An unrelated subsequent quotation ends the current exchange.
Inline/unmarked citations use conservative text boundaries; extended reproductions
show the matched text rather than an entire repost. These structural boundaries
are not automatic semantic interpretations of continuous prose. Every displayed
excerpt is an exact character slice of the preserved post, and the complete post
remains one click away. Repeated quotes in different exchanges have separate IDs.

Run `python -m unittest test_passage_notes.py -v` to check distinct quotations,
shared replies, nested quotations, same-paragraph exchanges, and separate anchors.

## 4chan quote responses

`source/tkg-responses.json` preserves the 402 selected post records, response categories, verbatim text and parent context. Run `python3 import-4chan.py` after the Usenet importer to rebuild this addition. The importer preserves existing source records, annotations and all 232 manifesto paragraphs. Matched or explicitly cited manifesto passages have margin annotations; other works and unresolved references are separate. The complete selected CSV is downloadable from the reader. `dist/4chan-import-audit.md` records the selection scope and limits.

## Usenet engagement selection

The reader retains 477 local exchanges from 344 of the 723 originally imported
Usenet records. The original messages and EML files remain untouched.
`curate-usenet.py` applies qualitative source decisions and extracts current-writer
responses adjacent to the quoted passage, separating inherited conversation from
new engagement. The compact version-15 baseline, decisions and selected exchange
slices are retained in `source/usenet-review/`.

For this edition, run `python3 curate-usenet.py` after the archival import steps.
Its baseline includes the existing periodical and 4chan additions; refresh that
baseline deliberately before using it after later content imports.
`dist/usenet-engagement-review.md` records selection scope and counts.
