# Dialogue manifest, version 1

Use exact image entry names from the source CBZ, including any directory prefix. The helper preserves all source pages, even when they have no manifest entry. Archive image names are naturally sorted, so `page-2.png` comes before `page-10.png`.

```json
{
  "version": 1,
  "title": "My Urdu dialogue edition",
  "source_language": "English",
  "pages": [
    {
      "file": "page-1.png",
      "regions": [
        {
          "id": "balloon-1",
          "kind": "dialogue",
          "source_text": "Zara, are you ready?",
          "text": "Zara، کیا تم تیار ہو؟",
          "preserve": ["Zara"],
          "box": [140, 150, 520, 290],
          "cleanup": [135, 145, 525, 295],
          "size": 38,
          "background": [1, 1, 1],
          "foreground": [0, 0, 0]
        }
      ]
    }
  ]
}
```

All coordinates are original source-image pixels from the top-left. `box` is the Urdu layout rectangle; `cleanup` is the source text area to cover and defaults to `box`. Keep both inside balloon contours. A wider cleanup rectangle can remove leftover slanted English letters without forcing the Urdu to fill that same width.

`kind` accepts `dialogue` or `monologue`. Do not add sound-effect, caption, or attack-call regions. `source_text` is optional but strongly recommended for translation review. The renderer records no inference about a region's meaning: classification is the translator's responsibility.

`preserve` lists exact English names that must remain inside `text`. Validation catches missing or changed names. It does not discover names automatically. English letter case is retained; set the desired source spelling in the manifest.

`size` is a positive starting size. `line-height`, scaling, and English-name spans affect fitting. The fitting report includes the effective size and scale. Fix unreadable text or clipping in the manifest before delivery; do not treat automatic shrinking as a quality check.

Color lists are RGB numbers from 0 to 1. For reverse lettering use `"background": [0,0,0]` and `"foreground": [1,1,1]`. Flat fills cannot reconstruct shaded drawings beneath the source text. If those areas require restoration, use an appropriate artwork-editing workflow and inspect the result.

Region IDs must be unique on each page. Duplicate page entries, unknown pages, invalid coordinates, missing names, malformed colors, empty text, and unsuitable fonts are rejected.
