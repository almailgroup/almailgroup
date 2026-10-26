# Images

All site images live under `assets/img/`. Replace a file by saving the new one **with the
same name**, then run `python3 tools/build.py`. The build lists the placeholders that are
still in place each time it runs.

## Placeholders to replace

### Background photos (`assets/img/photos/`)

These are rendered stand-ins, not photographs. Supply dark architecture photography at
about **1920 × 1080 px, JPEG, under ~300 KB**. Each section darkens its photo with a 50–72%
black overlay, so the photo itself can be a normal exposure.

| File | Section | What it should show |
| --- | --- | --- |
| `ceo-high-rise-window.jpg` | CEO quote | A man in a suit at a high-rise window |

Each also has a `-960.jpg` copy (960px wide) that phones load instead. When you replace a
photo, either save a 960px-wide copy of it over the `-960.jpg` file or delete that file.

### Logos (white on a transparent background, PNG)

Logos are shown white on black, so supply white artwork with a transparent background, about
500px wide.

| File | Logo |
| --- | --- |
| `logos/logo-azsco-systems.png` | AZSCO Systems |
| `logos/logo-mailarti.png` | Mailarti |
| `logos/logo-gemellry.png` | Gemellry |
| `logos/logo-shiplee.png` | Shiplee |
| `clients/logo-xcite.png` | Xcite |
| `clients/logo-arkan-al-kuwait.png` | Arkan Al Kuwait Real Estate |

## Real assets already in place

- **Almail Group logo** (`logos/logo-almail-group-white.png`): the white dhow mark, trimmed and
  made solid white. The favicons (`favicon-32.png`, `favicon-192.png`, `apple-touch-icon.png`)
  are that mark on a near-black square, and `og-share.jpg`, the card shown when a link is
  shared, is the hero photo darkened with the mark and the name. Remake those four if the logo
  changes.
- **Hero photo** (`photos/hero-glass-towers.jpg` and its `-960.jpg` copy): glass towers at dusk,
  supplied by Almail Group.
- **Why Choose photo** (`photos/why-choose-towers.jpg` and its `-960.jpg` copy): two towers
  at dusk, seen from below, supplied by Almail Group. On a phone it is cropped toward the left
  tower (`.why .bg img` in the stylesheet), since a narrow crop of the middle is only sky.
- **About photo** (`photos/about-curved-facade.jpg` and its `-960.jpg` copy): a curved glass
  tower at dusk, seen from below, supplied by Almail Group.
- **Sectors photo** (`photos/sectors-glass-facade.jpg` and its `-960.jpg` copy): a glass facade
  at night, supplied by Almail Group. It is far darker than the others, so the section's overlay
  is 55% rather than 72% and its intro is full white; every line was measured at its worst
  point against the photo (the intro 5.2:1, the sector names 4.7:1 and up).
- **Footer photo** (`photos/footer-skyscrapers-bw.jpg` and its `-960.jpg` copy): towers seen
  from below, supplied by Almail Group in colour. The stylesheet shows it in black and white
  (`.footer-photo img` in `assets/css/style.css`); take out `grayscale(1)` there for colour.
- **Partners** (`partners/`): Motorola, Ajax, Rasilient, Avigilon, Teltonika, Inrico, Hikvision
  and Pelco, cut from the partner logo sheet the AZSCO site used.
- **Clients** (`clients/`): the other 19 clients, cut from the AZSCO client logo sheet. That
  sheet was low resolution, so sharper originals are worth swapping in when you have them;
  Ewan Complex especially.
  `logo-al-asima.png` is the Arabic calligraphy mark from that sheet; please confirm it is Al Asima.
- **Group companies** (`logos/`): AZSCO Security (from the AZSCO site), Bizarri (the Bizarri
  Chalet logo from the Bizarri repository) and Netlet (from the Netlet repository, its orange
  roof made white to match).

## Before uploading

- Only upload photographs Almail Group owns or has licensed. Stock images taken from a search
  engine are a copyright risk.
- Keep photographs under about 300 KB. A 4 MB photo straight from a camera noticeably slows the
  page on mobile data.
