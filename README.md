# Almail Group — Website

The Almail Group website: a holding group company in Kuwait whose companies cover real estate,
construction and maintenance, low voltage technologies, jewelry design, e-commerce, security
systems and guarding, smart home solutions, and delivery.

Built as plain HTML, CSS and vanilla JavaScript with no build dependencies, so it can be
served from any static host (GitHub Pages, S3, Netlify, nginx) by copying the repository root.

## Pages

| Page | URL | Status |
| --- | --- | --- |
| Home: hero, why choose us, about and group companies, sectors, partners, CEO quote, clients | `/` | Complete |
| Almail Group World | `/almail-group-world/` | Stub |
| Our Sectors (lists the eight sectors) | `/our-sectors/` | Stub |
| News | `/news/` | Stub |
| Careers | `/careers/` | Stub |
| Contact: phone, email, address, opening hours | `/contact/` | Complete |
| Not found | `/404.html` | Complete |

Stub pages share the header, footer and styling so the navigation works, and say the page is
coming soon. They carry `noindex` and are left out of `sitemap.xml` until they have content:
set `"stub": False` for the page in `STUBS` (`tools/build.py`) when you fill it in.

## Structure

```
.
├── index.html, contact/index.html, news/index.html, ...   # generated pages
├── 404.html
├── assets/
│   ├── css/style.css     # all styling: tokens, sections, responsive rules
│   ├── js/main.js        # sticky header, mobile menu, scroll reveal, quote slider
│   ├── fonts/            # Inter and Montserrat, served from the site (see its README)
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
- **Group companies, partners, clients**: `SUBSIDIARIES`, `PARTNERS` and `CLIENTS`, each a list
  of `(name, image)`. The name is the logo's alt text.
- **Sectors**: `SECTORS` and `SECTORS_INTRO`.
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
  whole photo. Which part of the photo the strip comes from is `PORTRAIT` in the tool.
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
  top, without the contact bar, and goes back to normal near the top of the page.
- The home page: the hero has two buttons (Explore our sectors, Contact us; `actions` in
  `HOME`), Why Choose lists six areas with an icon each (`areas` in `WHY`), the sectors are
  numbered rows, and the partners sit in a grid of hairline cells.
- Sections fade and slide in as they scroll into view. Everything is visible with JavaScript
  off, and the motion is skipped for visitors who ask for reduced motion.
- Breakpoints at 1080px (hamburger menu and call button), 900px (one column for Why Choose,
  About, the sectors and the footer; fewer logos to a row) and 640px (phone layout: the sectors
  intro left-aligned, the clients three to a row).

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
