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
│   ├── js/main.js        # mobile menu, scroll reveal, quote slider
│   └── img/
│       ├── logos/        # Almail Group and group-company logos (white)
│       ├── partners/     # partner logos (white)
│       ├── clients/      # client logos (white)
│       ├── photos/       # full-bleed background photography
│       └── favicon-*.png, apple-touch-icon.png, og-share.jpg
├── tools/build.py        # regenerates every page and sitemap.xml
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

CSS and JavaScript are edited directly in `assets/`; the builder does not touch them.

## Images

Replacing an image is a matter of saving the new file over the old one with the same name, then
running `python3 tools/build.py` so the `width`/`height` attributes match the new file.

Several images are **placeholders** until the real ones are supplied. The build lists whichever
are still in place every time it runs. It recognises each placeholder by its exact contents, so a
replaced file drops off the list by itself. See `assets/img/photos/README.md` for the list,
sizes and naming.

Background photos can have an optional 960px-wide copy beside them (`hero-glass-towers-960.jpg`
next to `hero-glass-towers.jpg`), which phones download instead of the full-size file. A
placeholder 960px copy is never used next to a real photo, so a replaced photo can't keep showing
the old placeholder on phones; the build tells you to replace or delete the leftover copy.

## Design

- Black and near-black surfaces, white type; full-bleed photographs under 50–72% black overlays.
- Headings in Questrial (H1 80px, H2 56px, both scaling down on small screens); navigation in
  Montserrat SemiBold 14px; body copy in the system's Avenir/Helvetica.
- The current page's navigation link is lavender (`#C9B8FF`); every other link is white.
- Sections fade and slide in as they scroll into view. Everything is visible with JavaScript
  off, and the motion is skipped for visitors who ask for reduced motion.
- Breakpoints at 1080px (hamburger menu), 900px (single-column about and footer, 2/3-column
  logo grids) and 640px (phone layout).

## Notes

- **Domain**: the site is published at `www.almailgroup.com`. `CNAME` tells GitHub Pages which
  domain to serve, and `SITE_URL` in `tools/build.py` uses the same address for canonical URLs,
  link previews and the sitemap. Change both together if the domain ever changes.
- **Fonts**: Questrial and Montserrat load from Google Fonts without blocking the first paint,
  with system-font fallbacks if that request fails.

## Browser support

Modern evergreen browsers. Layout uses CSS grid, flexbox and custom properties; JavaScript is
ES5-style with `IntersectionObserver` feature detection.
