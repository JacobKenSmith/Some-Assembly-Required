# Some Assembly Required — complete source export

This is a portable copy of deployed **version 16**, verified against its saved source commit on 20 November 2026.

- Original site: https://circulation-atlas-jacob-smith.eragon97.chatgpt.site
- Source commit: `ead7b63473b6edc0b9f11c47ce4135d31529f0dd`
- Saved version: `appgprj_6af129c7089c8191b5c0b950d245db55~appgver_4ba17bf3af4c8191b646a2c42e628ee5`
- Deployment: `appgdep_6af4df6413ac8191a06dc133e435a903`

All 3,018 tracked files from that commit are included **byte for byte**. The website files have not been redesigned, regenerated, simplified, or changed. The only additions are this export guide and the `export/` provenance and verification files. Git internals, credentials, caches, and temporary workspace files are excluded.

## Run locally

Install Python 3 if it is not already installed. In the extracted project directory, run:

```sh
python3 -m http.server 8000 --directory dist
```

On Windows, the equivalent command is:

```powershell
py -m http.server 8000 --directory dist
```

Open `http://localhost:8000/`. Use a local HTTP server rather than double-clicking `index.html`: the reader fetches local Usenet JSON files, and browsers restrict those requests under `file://`.

No package installation, frontend build, API key, database, or ChatGPT account is required. Python is only a convenient local web server; production hosting does not require Python.

## Host independently

Upload the **contents of `dist/`** to any ordinary static web host, keeping every filename and subdirectory intact. Set the publish/document-root directory to `dist`. There is no build command. Serve HTML, CSS, JavaScript, JSON, images, fonts, CSV, Markdown, and EML files normally. A case-sensitive filesystem is supported; do not change filename case. Do not enable an authentication requirement or a blanket rewrite that serves `index.html` in place of existing JSON/source files.

For repository-based static hosting, retain this complete project and configure `dist` as the publish folder. For drag-and-drop static hosting, upload `dist` itself or its contents, as required by that host. The repository root is not the website root.

### Passage-specific links

The reader uses URL fragments, for example:

```text
/#p1/4chan-250550578-response-1
/#p1/usenet-post-20601-8faa2e13-engagement-1
```

Those paragraph and annotation IDs are unchanged. After moving hosts, replace only the URL before `#`; preserve the complete fragment. Browser navigation, section jumps, filters, source-context pages, and one-active-note behavior use the original JavaScript. No server-side router or special fragment rewrite is needed. Old links on the original domain will continue to point there unless that domain is redirected; this export cannot change them.

## Included content

- `dist/index.html`, `edition.css`, `edition.js`: the current reader, typewriter design, layout, navigation, and interactions.
- `dist/edition-data.json` and `edition-data.js`: the complete 232-paragraph primary text, original notes, annotations, IDs, source metadata, section data, and selection statistics.
- 827 primary-text annotation records, including 477 Usenet engagement annotations and 334 4chan annotations, plus 16 prior annotations; 113 additional entries for other writings or unresolved passages.
- `dist/usenet/posts/`: 723 preserved Usenet messages in HTML, JSON, and original EML formats. The reader selection remains 344 messages; excluded messages are retained as archival context, exactly as in the deployed version.
- `dist/4chan/posts/`: 402 selected posts with HTML/JSON context pages.
- `dist/Kaczynski_quote_responses.csv` and audit/selection records.
- `dist/assets/`: existing images and locally bundled Courier Prime regular, bold, and italic fonts, including their font license.
- `source/`: preserved base-text HTML, pilot edition, selected Usenet and 4chan data, extraction provenance, version-15 baseline, and engagement-selection decisions.
- Original Python import, extraction, build, and test scripts; original README; original hosting manifest; all retained older assets/code, even those not used by the current entry page.

This exports the data shipped with this website. It is not a new acquisition of every source it cites: full externally linked periodicals, other books, the entire original Usenet MBOX, wider 4chan dumps, and uncollected image dumps are not part of the deployed website. The complete primary manifesto and the excerpts/context used in its annotations are included.

## Dependencies and portability findings

| Item | Dependency status |
| --- | --- |
| ChatGPT hosting | Not required at runtime. `.openai/hosting.json` records the original platform project ID and `dist` publish directory. Retained unchanged for provenance; other static hosts can ignore it. Do not use it to overwrite the original hosted project. |
| Database, server-side services, authentication, API keys | None found in the current reader or its hosting manifest. No database export, environment variables, or secret configuration is needed. |
| Browser runtime | Modern JavaScript/CSS browser and HTTP(S) static hosting. The reader fetches same-origin JSON files from the bundled Usenet source directory. |
| Fonts and images used by the reader | Bundled locally. No Google Fonts request is needed by `index.html` / `edition.css`. |
| External citations and archives | Source links still point to their original public websites. Clicking them requires internet access and depends on those sites remaining available; their targets have not been rewritten. The base-text attribution is a link, not a runtime text download. |
| External magazine scan | The retained `passageScan` link points to a Ted K Archive image. It opens externally when clicked; the reader's magazine image asset is also bundled locally. The external link is preserved exactly. |
| Older retained code | `dist/style.css` contains a Google Fonts import for the older design. The current entry page does not load that stylesheet. Older data includes citation/Library links; these are historical links, not current reader data services. |
| Research/build scripts | Standard-library Python scripts are preserved as source. Historical `build-data.py` and `build-edition.py` contain absolute paths to the original research workspace and cannot be assumed runnable without those inputs. They are unnecessary for serving this version. Do not run historical builders as a deployment step. |
| Content regeneration | The finished `dist` tree is the authoritative deployable snapshot. `curate-usenet.py` uses its included baseline; import/build scripts can intentionally change data, ordering, and IDs. Back up the snapshot before using them. |

No additional licensing rights are conferred by the export. Source attributions, original material, and bundled font licensing are retained.

## Verify the copy

Run from the extracted project directory:

```sh
python3 export/verify_export.py
```

This checks every original file against its SHA-256 digest, validates packaged HTML references and local source-data references, confirms annotation sources and the example deep-link IDs, and reports the preserved counts. `export/SOURCE_SHA256.json` covers all original tracked files. `export/EXPORT_PROVENANCE.json` records the version and verification scope.

Export checks passed: all original file bytes match the deployed source commit; 10,105 local HTML references resolve; all local source files referenced by edition metadata exist; current reader JavaScript passes Node's syntax check; all six original quotation-segmentation unit tests pass. Visual/browser testing was not repeated for this export because the deployed website files are unchanged.
