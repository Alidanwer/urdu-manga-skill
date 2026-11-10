# Urdu manga workflow

## Inspect and transcribe

Read the user's scope first. Start from the original CBZ, inspect its page order, and generate numbered PNGs plus a contact sheet using `manga.py inspect`. The contact sheet is a navigation aid; read full-size source pages before translating. Record each balloon's source dialogue and coordinates in the manifest. OCR may assist transcription when available, but verify it against the image, especially names and small lettering.

## Classify and translate

Translate speech and meaningful internal monologue. Retain English proper names within the sentence. Leave action sounds, standalone named attacks, nonverbal cries, captions, cover lettering, and credits untouched by default. A command containing a name can still be dialogue: translate the command and retain the name. A balloon containing only a named technique should generally remain original.

Adapt tone and idiom into natural Urdu while preserving meaning, register, and character voice. Keep a small terminology list for recurring names and technical terms. Do not replace an English technique name with a Japanese transliteration unless requested. Do not claim Japanese-source accuracy when working from an English scan.

## Verify the font

Check actual Urdu glyphs, not the filename. Run `validate` with the candidate font, then render representative long/short balloons and mixed-name dialogue. The originating workflow accepted PDMS Nastaliq Nafees Regular after testing. An earlier FreeHand font lacked the standard Urdu glyphs needed by the renderer. That finding applies to the tested file, not every font with a similar family name.

Nastaliq often needs more vertical room than compact manga lettering. Leave clearance for descending diagonals and dots. The renderer uses MuPDF Story's shaping/layout, a transparent raster text layer, and optional modest overprinting for extra weight. It does not distribute the font binary. Supply fonts separately under their terms.

## Clean and letter

Use separate cleanup and layout rectangles where the source letters are slanted. Keep source balloon borders and tails intact. White fill is suitable inside a white balloon; it will create visible patches over textured artwork. Do not promise to recover hidden art through a flat fill.

English spans must keep their original spelling and left-to-right direction inside the Urdu paragraph. Check apostrophes, punctuation, adjacent Urdu particles, and name wrapping visually. The renderer defaults to English at 65% of the Urdu starting size; adjust the source text/layout if a name overwhelms its balloon.

Reverse lettering must remain white over black. The black-on-black failure caught in the original project is why foreground color is an explicit manifest field and tested behavior.

## Export and review

Render each page with original proportions, producing ordered PNGs, a flattened PDF, a CBZ, the manifest, a contact sheet, and a fitting report. Default output is 1.5× the source pixel dimensions; this sharpens newly placed lettering but does not add detail to the source drawing. Flattening means dialogue is not selectable/searchable PDF text.

Review every changed page at a readable size and compare with the source. Look for clipped Urdu descenders, broken joining, missing English names, unreadable shrinking, leftover English fragments, accidental edits to action lettering, and cleanup crossing panel boundaries. Readability warnings in `fit-report.json` require inspection; they are heuristics, not proof of failure or success.

Check page counts and archive integrity, then provide outputs with a preview and known limitations. Keep older editions intact. The helper rejects a nonempty output folder unless `--overwrite` is explicit; use a fresh folder for normal revisions.

## What is automated

The helper automates archive reading, manifest validation, glyph checks, text shaping/fitting, page export, contact sheets, and archive validation. An assistant or translator supplies transcription, interpretation, Urdu wording, classification, cleanup choices, and final visual review.

The original project used the PDF skill for authoring/review, OpenAI Docs for a separate model-choice answer, and ImageGen for an attempted repair that was rejected. No image-generation output was incorporated. This reusable skill does not require those exact plugins; use the relevant available document/image capabilities for the task.
