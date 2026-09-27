---
name: html-report-keyword-index
description: >-
  Build a "keyword → original source text" cross-reference index for a suite of static
  HTML report pages. Use this skill when the user wants to auto-extract keywords from
  report content (characters, places, terms) and let readers click an index entry to
  jump to the source-text page, scroll to the exact location, and highlight every
  occurrence of that keyword. Covers the local-file (file://) fetch constraint,
  idempotent widget injection into many pages, and reader-page deep-linking.
agent_created: true
---

# HTML Report Keyword → Source Index

## Purpose

Turn a set of generated HTML report pages into a cross-reference system: a keyword
index (typically named entities such as people/places extracted from the analysis
data) where clicking an entry opens the original full-text reading page, scrolls to
the keyword's location, and highlights every occurrence — enabling fast "report ↔
source" comparison.

## When to use

- The user asks to "build a keyword index for the reports", "link report terms to the
  original text", "highlight keywords in the source when clicked", or similar
  cross-reference / navigation features across a static HTML report suite.
- There is a single authoritative source-text page (e.g. a reader generated from a
  plain-text manuscript) and many derived report pages that discuss the same entities.

## Workflow

### 1. Choose and extract the keyword corpus
Source keywords from the analysis pipeline that produced the reports (most reliable
and guaranteed to also exist in the source text): e.g. character stats JSON, spatial
/ location-node dict, tag vocabularies. Avoid ad-hoc NLP extraction unless no
structured entity list exists.
- Deduplicate by surface form; keep the first-assigned type.
- For each keyword, **scan the full source text** to compute: total occurrences
  (substring `count`), number of sections/chapters present, and the first occurrence
  `(section, paragraph_offset)`. These stats must use the *same* matching rule as the
  highlight step below (substring match) so counts and highlights agree.

### 2. Emit a data artifact AND a self-contained widget — never fetch() locally
**Critical constraint:** reports are opened via `file://`, where browsers block
`fetch()` of local JSON (CORS / "Cross origin requests are only supported for http…").
Do **not** load the index via `fetch()`. Instead:
- Write a readable `keywords.json` for transparency (optional).
- **Embed the same data directly inside the widget JS** (`var DATA = {...};`) so the
  widget is self-contained and works offline. Generate both from one script to avoid
  drift. Escape `<` as `\u003c` in the embedded JSON to be safe inside `<script>`.
- The widget renders a card: title, search box (name substring filter), type tabs
  (e.g. 全部/人物/地点), and a grid of items showing `命中 N 处 · 涉及 M 回 · 首现 X`.
  Clicking an item does `window.open('SOURCE_PAGE.html?kw='+encodeURIComponent(name),'_blank')`.

### 3. Enhance the source-text reader for deep-link + highlight
Add stable paragraph anchors (`id="secN-pM"`) to every `<p>` in the reader. Add a
script that reads the URL query:
- `?kw=NAME`: walk `.chapter p, .foreword p` (or equivalent), and for each paragraph
  whose `textContent` contains the keyword, rebuild its `innerHTML` wrapping matches
  in `<mark class="kw-hl">` (use `textContent` + manual escaping; regex-escape the
  keyword's special chars: `/[.*+?^${}()|[\]\\]/g`). Show a floating bar with total
  count + 上一条/下一条 (prev/next `scrollIntoView`) + 取消高亮 (unwrap marks).
- `?loc=secN-pM`: scroll to that specific paragraph (e.g. when arriving from a chart
  node click); still highlight the keyword.
- Style `mark.kw-hl` with CSS variables so it adapts to light/dark themes.

### 4. Inject the widget into the report pages (idempotent)
For each report HTML, inject (before `</body>`) an idempotent block wrapped in anchor
comments (e.g. `<!--WZ-KEYINDEX-START/END-->`). Skip files already containing the
anchor, and exclude the reader page, the index page itself, and non-HTML assets.
The block is just `<div id="wz-kwindex"></div>` + `<script src="keyword-index-widget.js"></script>`.
- Verify the dark-mode toggle and other existing scripts remain intact after injection.

### 5. Validate
- `node --check` the widget JS and the reader's inline highlight script.
- Parse each generated HTML with an HTML parser to confirm tags balance (no stray
  close tags, no unclosed elements).
- Confirm the reader paragraph count matches expectations and `id`s are unique.

## Key gotchas
- **file:// fetch is blocked** → embed data in the widget JS (see step 2). This is the
  single most common failure for local HTML report suites.
- **Highlight vs count consistency**: use the identical matching rule (substring) in
  both the Python stats scan and the JS highlight, or the displayed count won't match
  the number of `<mark>`s.
- **Single-character keywords** (e.g. a one-char place name) will match inside longer
  words (substring) — this is expected; document it.
- **Regex-escaping** the keyword in JS is mandatory or names containing `.`/`+`/etc.
  break the highlight regex.
- **Idempotency**: always guard injections with an anchor comment so re-running the
  generator doesn't duplicate the widget or clobber the dark-mode script.

## Reusable assets
- `scripts/` — place the generator(s) here when packaging: one script that emits both
  `keywords.json` and the embedded-data `keyword-index-widget.js`, and one idempotent
  injector for the report pages. Keep them deterministic (re-runnable) and back up any
  overwritten data files first.
