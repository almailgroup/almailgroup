# Fonts

The site serves its two typefaces itself rather than from Google Fonts, so a visitor's phone
doesn't have to look up and connect to two more servers before the text can be drawn.

| File | Typeface | Used for | Weights |
| --- | --- | --- | --- |
| `inter-latin.woff2` | Inter | Body text | 400 to 600 (variable) |
| `montserrat-latin.woff2` | Montserrat | Headings, navigation, buttons | 100 to 900 (variable) |

Both are the Latin files Google Fonts serves (Inter v20, Montserrat v31), covering English and
Western European characters. Inter is cut down to the 400 to 600 weights the site uses, which
makes it a quarter smaller; doing the same to Montserrat made it larger, so it is as Google
serves it.

The `@font-face` rules are at the top of `assets/css/style.css`, together with the
size-adjusted Arial fallbacks the page shows while the fonts load, so the text barely moves
when they arrive.

## Licence

Both typefaces are under the SIL Open Font License 1.1 (https://openfontlicense.org), which
allows using them on a website and serving them from it:

- Inter: Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)
- Montserrat: Copyright 2011 The Montserrat Project Authors (https://github.com/JulietaUla/Montserrat)

The copyright and licence notices are also kept inside each font file.
