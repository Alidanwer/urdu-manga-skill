---
name: urdu-manga
description: Translate and typeset manga or comic dialogue into Urdu while preserving original artwork, English proper names, attack calls, and sound effects. Use for Urdu comic localization and revisions of lettered CBZ editions.
---

# Urdu Manga

Produce an Urdu reading edition from the user's source pages. Translate dialogue and meaningful internal monologue; preserve the original drawings and page order.

## Accepted lettering preferences

- Keep character, place, organization, and technique names in their original English spelling. Translate only the surrounding dialogue.
- Leave standalone attack calls, action sounds, laughter, breath sounds, nonverbal cries, captions, headings, cover titles, logos, credits, and bonus notes as source lettering unless the user requests otherwise.
- Use idiomatic conversational Urdu with the original emotion and intent. Do not shorten away meaning to fit a balloon.
- Prefer the user's PDMS Nastaliq Nafees font when available. Accept another requested Urdu-capable font after checking its actual glyph coverage and joined rendering. Font files are local inputs and are not bundled.
- These are defaults from the originating user's workflow. A current user's explicit preferences override them.

## Work from the source

For revisions, restart from the original archive and apply the approved dialogue manifest. This restores untranslated lettering without layering new edits over previous replacements.

Read [workflow.md](references/workflow.md) when beginning a conversion. It covers reading pages, classifying text, translation, cleanup, and visual review. The renderer does not recognize speech balloons or translate text automatically.

For a CBZ, use the helper to inspect pages and create a manifest skeleton:

```sh
python scripts/manga.py inspect --source book.cbz --output work/inspection
```

Read the source pages at readable size, then prepare the UTF-8 manifest using [manifest.md](references/manifest.md). Record source text, Urdu text, preserved names, and explicit cleanup/text rectangles. Do not invent dialogue from a contact sheet or memory.

## Render and review

Validate before rendering:

```sh
python scripts/manga.py validate --source book.cbz --manifest dialogue.json --font /path/to/urdu.ttf
python scripts/manga.py render --source book.cbz --manifest dialogue.json --font /path/to/urdu.ttf --latin-font /path/to/latin.ttf --output output/edition
```

The script shapes Urdu through MuPDF Story, isolates English name spans, fits the paragraph, renders the supplied font to a transparent text layer, and exports flattened PDF/CBZ pages. It supports regular-font thickening, separate cleanup rectangles, reverse white lettering, natural archive ordering, and a fitting report. Readability warnings require review; a successful fit is not proof of good typography.

Inspect every changed page, including small balloons, mixed English/Urdu text, names, punctuation, Nastaliq descenders, and reverse lettering. Confirm untouched action lettering and page order. Compare suspicious patches against the original at the same scale. Adjust the manifest and rerender as needed. Do not silently replace an unsuitable font or claim pixel-identical artwork when cleanup patches remain visible.

Provide the PDF, CBZ, manifest, and a preview. State the source language used for translation and any remaining layout limitations. Keep originals and earlier editions intact.

## Boundaries

The bundled helper handles image-based CBZ archives. For PDF, EPUB, CBR, or another input, first choose an appropriate extraction workflow that preserves original page order and resolution; do not pretend the CBZ helper accepts it directly.

Use document typesetting for deterministic lettering. If raster artwork restoration is needed, use an available image-editing tool, review the result against the source, and do not regenerate an entire page merely to replace dialogue. Publishing a skill does not authorize publishing the user's manga scans, font binaries, or translated books.
