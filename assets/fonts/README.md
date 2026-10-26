# Fonts

The site serves its typefaces itself rather than from Google Fonts, so a visitor's phone
doesn't have to look up and connect to two more servers before the text can be drawn.

| File | Typeface | Used for | Weights |
| --- | --- | --- | --- |
| `inter-latin.woff2` | Inter | Body text | 400 to 600 (variable) |
| `montserrat-latin.woff2` | Montserrat | Headings, navigation, buttons | 100 to 900 (variable) |
| `tajawal-arabic-400.woff2`, `tajawal-arabic-700.woff2` | Tajawal | Arabic body text | 400, 700 |
| `cairo-arabic.woff2` | Cairo | Arabic headings, navigation, buttons | 200 to 1000 (variable) |

The Arabic files are Google Fonts' Arabic subsets (Cairo v31, Tajawal v12), about 50 KB
together. Their `@font-face` rules carry the Arabic `unicode-range`, so a browser fetches them
only for Arabic letters: the English pages never download them, and a Latin word on an Arabic
page is drawn in Montserrat or Inter.

Inter and Montserrat are the Latin files Google Fonts serves (Inter v20, Montserrat v31), covering English and
Western European characters. Inter is cut down to the 400 to 600 weights the site uses, which
makes it a quarter smaller; doing the same to Montserrat made it larger, so it is as Google
serves it.

The `@font-face` rules are at the top of `assets/css/style.css`, together with the
size-adjusted Arial fallbacks the page shows while the fonts load, so the text barely moves
when they arrive.

## Licence

All four typefaces are under the SIL Open Font License 1.1 (https://openfontlicense.org), which
allows using them on a website and serving them from it:

- Inter: Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)
- Montserrat: Copyright 2011 The Montserrat Project Authors (https://github.com/JulietaUla/Montserrat)
- Cairo: Copyright 2009 The Cairo Project Authors (https://github.com/Gue3bara/Cairo)
- Tajawal: Copyright 2017 Boutros International

The copyright and licence notices are also kept inside each font file.
