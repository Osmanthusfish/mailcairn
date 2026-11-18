# Bundled fonts

Retrieved 2026-11-09 from the Google Fonts repository. These are unmodified
variable TTF files, served from the local application; no Google Fonts API or
CDN request is made at runtime. Both use SIL Open Font License 1.1. Full original
copyright and license texts accompany the binaries in `mailcairn/static/fonts/`.
The OFL permits embedding and redistribution with software, including commercial
software, with its conditions and notices preserved. Font rights remain OFL and
are separate from the application's PolyForm Noncommercial license.

| File | Source | SHA-256 |
| --- | --- | --- |
| HankenGrotesk.ttf (132,892 bytes) | [Google Fonts source](https://github.com/google/fonts/blob/main/ofl/hankengrotesk/HankenGrotesk%5Bwght%5D.ttf) | `813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f` |
| Newsreader.ttf (451,664 bytes) | [Google Fonts source](https://github.com/google/fonts/blob/main/ofl/newsreader/Newsreader%5Bopsz%2Cwght%5D.ttf) | `8a08d13f8a6c0d51be379a60af84f945f65369a67e509ee3c3bdcc421254d7c1` |

Hanken Grotesk is used for controls, metadata and message text; Newsreader is
used for the brand and display headings. CSS fallbacks and `font-display: swap`
keep text available if a font fails to load. Both binaries total 584,556 bytes;
no subset or conversion was performed. English glyphs use these fonts; Chinese
message content continues to use available system glyph fallbacks.
