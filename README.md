# Almail Group — Website

The Almail Group website: a holding group company in Kuwait whose companies cover real estate,
construction and maintenance, low voltage technologies, jewelry design, e-commerce, security
systems and guarding, smart home solutions, and delivery.

Built as plain HTML, CSS and vanilla JavaScript with no build dependencies, so it can be
served from any static host (GitHub Pages, S3, Netlify, nginx) by copying the repository root.

## Pages

| Page | URL | What is on it |
| --- | --- | --- |
| Home | `/` | Hero, why choose us, about and the group companies, sectors, partners, CEO quote, clients |
| Almail Group World | `/almail-group-world/` | A card per company: what it does, its sectors, its website |
| Our Sectors | `/our-sectors/` | The eight sectors, what each covers and the companies working in it |
| News | `/news/` | News items, newest first, and who to email for media enquiries |
| Careers | `/careers/` | Open positions, how to apply, and the companies to work for |
| Contact | `/contact/` | Call, email, visit and opening hours, and the companies' own websites |
| Not found | `/404.html` | A way back to the home page in each language |

Every page is in English and Arabic: English at the addresses above, Arabic under `/ar/`
(`/ar/`, `/ar/contact/`, ...). See **Languages** below.

On the home page each sector opens its card on Our Sectors, and each company logo opens its
card on Almail Group World; the card arrived at is outlined in lavender. Every inner page ends
with a "Talk to us" band with call and email buttons.

## Structure

```
.
├── index.html, contact/index.html, news/index.html, ...   # generated pages, English
├── ar/                   # the same pages in Arabic
├── 404.html
├── assets/
│   ├── css/style.css     # all styling: tokens, sections, responsive rules
│   ├── js/main.js        # sticky header, mobile menu, back to top, scroll reveal, photo previews, quote slider
│   ├── fonts/            # Inter, Montserrat, Cairo and Tajawal, served from the site (see its README)
│   └── img/
│       ├── logos/        # Almail Group and group-company logos (white)
│       ├── partners/     # partner logos (white)
│       ├── clients/      # client logos (white)
│       ├── photos/       # full-bleed background photography
│       └── favicon-*.png, apple-touch-icon.png, og-share.jpg
├── tools/build.py        # regenerates every page and sitemap.xml
├── tools/images.py       # makes the lighter image copies phones load (needs Pillow)
├── tools/derived-images.json  # which original each of those copies was made from
├── robots.txt
└── sitemap.xml
```

## Languages

The site is in English and Arabic, built from one set of templates in `tools/build.py`. Every
visible string there is a pair, `("English", "Arabic")`, so the two versions cannot drift
apart; a string that is the same in both, a brand name or a phone number, is written once.
Adding content means giving both halves: a news item's title and paragraphs, a job, a
company's description.

- **Addresses**: English at the root (`/contact/`), Arabic under `/ar/` (`/ar/contact/`).
  Each page tells search engines about its twin (`hreflang`), and both are in `sitemap.xml`.
- **Switching**: the top bar and the phone menu carry a link to the same page in the other
  language, named in that language ("العربية" on an English page, "English" on an Arabic one).
- **Right to left**: Arabic pages are `dir="rtl"`. The layout mirrors by itself because the
  stylesheet uses logical sides (start and end rather than left and right); the "right to
  left" block in `assets/css/style.css` handles what direction alone does not: the menu
  sliding in from the left, arrows, the hero's shading, letter spacing (none in Arabic) and
  taller line heights. Phone numbers and emails are kept left to right inside Arabic text.
- **Type**: Arabic is set in Cairo (headings) and Tajawal (text), the pair the AZSCO site
  uses, served from `assets/fonts/`. They cover only Arabic letters, so Latin words on an
  Arabic page stay in Montserrat and Inter, and English pages never download them.
- **Names**: the Arabic names are the ones the companies use themselves: مجموعة الميل,
  أزسكو للأمن, أنظمة أزسكو الأمنية, بيزاري and نت‑لت. Shiplee, Gemellry and Mailarti keep their
  Latin names until they have Arabic ones. The Arabic address is the one AZSCO's site gives
  for the same building.

The Arabic text was written for this site; have a native speaker read it before relying on
it for anything formal.

## Running locally

Serve the folder rather than opening `index.html` directly: the clean URLs (`/contact/`)
rely on directory-index resolution, which only a real server provides.

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Editing

All page content, the navigation and the contact details live in `tools/build.py`. After
editing it, regenerate the HTML:

```bash
python3 tools/build.py
```

- **Contact details**: `PHONE`, `EMAIL`, `ADDRESS` and `HOURS` at the top of the file.
- **Social links**: `INSTAGRAM_URL` and `X_URL`. While empty, the footer icons link to `#`.
- **Companies**: `COMPANIES`, one entry each: name, logo, field, a description, the sectors it
  works in and its website (leave `url` empty for none). The Almail Group World page, the
  sector cards and the home page's logo row all read from it. A company with no description
  yet says "More about ... soon".
- **Partners, clients**: `PARTNERS` and `CLIENTS`, each a list of `(name, image)`. The name is
  the logo's alt text.
- **Sectors**: `SECTORS` (the names and their order), `SECTOR_INFO` (an icon and a
  description each) and `SECTORS_INTRO`.
- **News**: `NEWS`, newest first: a date, a title and one string per paragraph.
- **Jobs**: `JOBS`, empty for now, so the Careers page says there are no openings and invites
  a CV. Add an entry (the format is in the comment above it) and it is listed with an
  "Apply by email" button. Applications go to `CAREERS_EMAIL`.
- **Page headings**: `INNER` has each inner page's title, the line under it, its search
  description and the photo behind it.
- **CEO quote slider**: `QUOTES`. Add another entry and the slider gets a second dot and starts
  rotating every 7 seconds (paused on hover or keyboard focus, and off for visitors who ask for
  reduced motion).

CSS and JavaScript are edited directly in `assets/`; run the builder afterwards, because it
writes the stylesheet into every page (a phone can then draw the page from the first response,
without waiting for a second request) and gives every page the current version of each file.
Scripts, fonts and images are asked for at an address carrying a version taken from the file's
contents (`main.js?v=1a2b3c4d5e`), so a browser holding an older copy cannot draw new pages
with it. GitHub Pages lets a browser keep a file for ten minutes, and before this a page could
arrive new while its photos came from the browser's copy of the last version.

## Images

Replacing an image is a matter of saving the new file over the old one with the same name, then
running both tools:

```bash
pip install Pillow          # once; 11.3 or later
python3 tools/images.py     # the lighter copies phones and modern browsers load
python3 tools/build.py      # the pages
```

`tools/images.py` makes, from each original:

- **Photos**: a 960px JPEG, AVIF copies at full size and 960px (about half the bytes of a JPEG
  that looks the same), and a tall strip at full resolution for phones held upright. A phone
  only shows a narrow strip of a wide photo, so it gets that strip, sharper and lighter than the
  whole photo. Which part of the photo the strip comes from is `PORTRAIT` in the tool. And a
  copy 32px wide, a few hundred bytes, kept inside `tools/derived-images.json` rather than as a
  file: the pages show it blurred while the photo loads (see Design).
- **Logos**: a lossless WebP copy, pixel for pixel the PNG at about two thirds of the size.

Pages offer these first and fall back to the original JPEG or PNG for a browser that takes
neither format. `tools/derived-images.json` records which original each copy came from, so a
photo replaced without running `tools/images.py` shows the new original everywhere (the build
says so) rather than the old picture on phones. On an iPhone the home page is about 0.6 MB
with every section scrolled into view, where it was 1.5 MB.

Several images are **placeholders** until the real ones are supplied. The build lists whichever
are still in place every time it runs. It recognises each placeholder by its exact contents, so a
replaced file drops off the list by itself. See `assets/img/photos/README.md` for the list,
sizes and naming.


## Design

- Black and near-black surfaces, white type; full-bleed photographs under 50–72% black overlays.
- Headings and navigation in Montserrat (H1 80px and H2 56px at weight 600, scaling down on
  small screens; the navigation 16px bold); body copy in Inter at 20px (18px on a phone).
- A contact bar runs along the top of every page: the address (opening Google Maps), the
  phone, the email and the social links. Below 1200px the address shortens, and on a phone
  the bar keeps the phone number and the social links. Its address and map link are
  `ADDRESS_LINE`, `ADDRESS_SHORT` and `MAPS_URL` in `tools/build.py`.
- The current page's navigation link is lavender (`#C9B8FF`); every other link is white.
- On phones and tablets the header has a call button beside the menu button, and the menu ends
  with a call button, the email, the address (opening Google Maps), the opening hours and the
  social links. While the menu is open the page behind it can't be reached by keyboard or
  screen reader.
- Hover effects only exist where there is a mouse or trackpad; on a touch screen a tap flashes
  lavender and buttons press in, and nothing stays lit after going Back. Every link and button
  is at least 44px to tap.
- Once the header has scrolled out of sight it comes back as a compact dark bar fixed to the
  top, without the contact bar, and goes back to normal near the top of the page. On phones
  and tablets that bar slides away while the reader scrolls down and returns as soon as they
  scroll up, so it doesn't take a tenth of the screen while reading.
- A round "back to top" button appears once a page has scrolled a screen and a half.
- On a desktop, the fixed header carries the language link too, since the top bar that holds it
  is hidden then. Every page's footer repeats the page links.
- Large screens (1680px and up, again at 2200px) get a wider column and larger type, so a
  1920 or 2560px monitor is filled the way a laptop is. The photos are 1672px wide, so on those
  screens they are enlarged; larger originals (2560px or more) would sharpen them.
- Tablets keep the desktop's two columns of sectors (from 800px) and four of partners (from
  760px).
- Moving between pages fades one into the next (Chrome, Edge, Safari 18+), and Chrome and Edge
  get a page ready in the background, fetched and drawn, as soon as the pointer rests on its
  link or a finger lands on it, so it opens at once.
- A photo further down a page never pops in over black: until it arrives its section shows a
  blurred preview of it, made from a 32px copy written into the page, and then the photo fades
  in over that. The hero and the page headings, fetched first, are drawn as soon as they arrive.
  The previews are drawn only once their section is within a screen of view, so the first paint
  never waits on them.
- The menu starts to slide the moment it is tapped; making the page behind unreachable and
  moving focus into it follow a frame later. The script reads nothing from the page's layout
  while it starts, so it doesn't hold up the first taps on a phone.
- The home pages describe the group to search engines (schema.org: name in both languages,
  logo, contact details, address, the companies).
- A phone on its side (a screen under 500px tall) gets a slim header without the contact bar,
  and smaller headings, so the hero's words and buttons fit on one screen.
- Added to a phone's home screen, the site has its own name and icon (`manifest.webmanifest`,
  and `ar/manifest.webmanifest` for the Arabic pages; icons `assets/img/icon-512.png` and
  `icon-maskable-512.png`, made from the logo).
- The home page: the hero has two buttons (Explore our sectors, Contact us; `actions` in
  `HOME`), Why Choose lists six areas with an icon each (`areas` in `WHY`), the sectors are
  numbered rows, and the partners sit in a grid of hairline cells.
- Sections fade and slide in as they scroll into view, in 0.7s (0.5s on a phone). Everything is
  visible with JavaScript off, and the motion is skipped for visitors who ask for reduced motion.
- Breakpoints at 1680px and 2200px (large screens), 1080px (hamburger menu and call button),
  900px (one column for Why Choose, About and the footer; fewer logos to a row), 800px (one
  column of sectors), 760px (two of partners) and 640px (phone layout: the sectors intro
  left-aligned, the clients three to a row).

## Notes

- **Domain**: the site is published at `www.almailgroup.com`. `CNAME` tells GitHub Pages which
  domain to serve, and `SITE_URL` in `tools/build.py` uses the same address for canonical URLs,
  link previews and the sitemap. Change both together if the domain ever changes.
- **Fonts**: Inter and Montserrat are served from the site itself (`assets/fonts/`), one
  variable file each, preloaded and never blocking the first paint. Until they arrive the page
  shows Arial resized to match them, so the text barely moves when they do.

## Browser support

Modern evergreen browsers. Layout uses CSS grid, flexbox and custom properties; JavaScript is
ES5-style with `IntersectionObserver` feature detection.
