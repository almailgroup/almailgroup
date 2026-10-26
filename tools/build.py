#!/usr/bin/env python3
"""Static builder for the Almail Group website.

Writes every page as plain HTML into the repository root, each in its own
directory (contact/index.html, news/index.html, ...) so addresses are clean:
/contact/, not /contact.html. Stdlib only -- nothing to install.

    python3 tools/build.py
"""
import datetime
import hashlib
import html
import os

# Output to the repository root (this script lives in <repo>/tools).
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

SITE_URL = "https://www.almailgroup.com"
SITE_NAME = "Almail Group"

# ---------------------------------------------------------------- contact
PHONE = "+965 - 1808606"
PHONE_HREF = "+9651808606"
EMAIL = "Info@Almailgroup.com"
EMAIL_HREF = "info@almailgroup.com"
ADDRESS = ["Kuwait Building Tower, Floor 27,", "Fahad Alsalem Street,", "Qibla City - Kuwait."]
HOURS = [("Sunday - Thursday", "8am - 5pm"), ("Friday", "Closed"), ("Saturday", "Closed")]

# Paste the profile URLs here and rebuild. Left empty, the icons still show
# but link nowhere ("#").
INSTAGRAM_URL = ""
X_URL = ""

# ---------------------------------------------------------------- routes
# Every page lives in its own directory so the address bar never shows
# ".html"; the home page is the bare site root.
ROUTES = {
    "index.html": "",
    "almail-group-world.html": "almail-group-world",
    "our-sectors.html": "our-sectors",
    "news.html": "news",
    "careers.html": "careers",
    "contact.html": "contact",
}

NAV = [
    ("Home", "index.html"),
    ("Almail Group World", "almail-group-world.html"),
    ("Our Sectors", "our-sectors.html"),
    ("News", "news.html"),
    ("Careers", "careers.html"),
    ("Contact", "contact.html"),
]


def path_for(fname):
    """Root-relative clean URL for a page: '/', '/contact/'."""
    if fname == "404.html":
        return "/404.html"
    slug = ROUTES[fname]
    return "/" if slug == "" else f"/{slug}/"


def out_file_for(fname):
    """File the page is physically written to, relative to OUT."""
    if fname == "404.html":
        return "404.html"
    slug = ROUTES[fname]
    return "index.html" if slug == "" else f"{slug}/index.html"


def link(spec):
    """'contact.html' or 'our-sectors.html#security' -> clean URL."""
    fname, _, anchor = spec.partition("#")
    return path_for(fname) + (f"#{anchor}" if anchor else "")


def e(text):
    return html.escape(text, quote=True)


# ---------------------------------------------------------------- images
IMG = "assets/img"


def _image_size(path):
    """(width, height) of a PNG or JPEG, read from the file itself so the
    width/height attributes always match what is on disk."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] == b"\x89PNG\r\n\x1a\n":          # IHDR is always the first chunk
        return (int.from_bytes(data[16:20], "big"),
                int.from_bytes(data[20:24], "big"))
    i = 2                                           # JPEG: walk to the SOF marker
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return (int.from_bytes(data[i + 7:i + 9], "big"),
                    int.from_bytes(data[i + 5:i + 7], "big"))
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    raise ValueError(f"{path}: no size marker found")


def small_version(rel):
    """'photos/hero.jpg' -> 'photos/hero-960.jpg' when that file exists, for
    phones. A placeholder small copy is only used beside a placeholder
    full-size photo, so replacing a photo can never leave phones showing the
    old placeholder."""
    stem, ext = os.path.splitext(rel)
    small = f"{stem}-960{ext}"
    if not os.path.exists(os.path.join(OUT, IMG, small)):
        return None
    if _is_placeholder(small) and not _is_placeholder(rel):
        return None
    return small


def srcset(rel):
    small = small_version(rel)
    if not small:
        return ""
    w_small = _image_size(os.path.join(OUT, IMG, small))[0]
    w_full = _image_size(os.path.join(OUT, IMG, rel))[0]
    return f"/{IMG}/{small} {w_small}w, /{IMG}/{rel} {w_full}w"


def img(rel, alt, cls="", lazy=True, priority=False, sizes=None):
    """An <img> with real width/height (no layout shift) and lazy loading by
    default. `rel` is relative to assets/img/. With `sizes`, a -960 copy of
    the file is offered to small screens when there is one."""
    w, h = _image_size(os.path.join(OUT, IMG, rel))
    attrs = [f'src="/{IMG}/{rel}"', f'alt="{e(alt)}"', f'width="{w}"', f'height="{h}"']
    if cls:
        attrs.insert(0, f'class="{cls}"')
    if sizes and srcset(rel):
        attrs += [f'srcset="{srcset(rel)}"', f'sizes="{sizes}"']
    if priority:
        attrs.append('fetchpriority="high"')
    elif lazy:
        attrs.append('loading="lazy"')
    attrs.append('decoding="async"')
    return "<img " + " ".join(attrs) + ">"


def backdrop(photo, priority=False, sizes="100vw"):
    """Full-bleed background photo. A real <img> rather than a CSS background,
    so it lazy-loads below the fold and the hero can be fetched early."""
    return (f'<div class="bg" aria-hidden="true">'
            f'{img("photos/" + photo, "", lazy=not priority, priority=priority, sizes=sizes)}</div>')


# Images that are stand-ins until the real files are supplied, with the SHA-1
# of the placeholder. Replace the file (same name) and it drops off the list
# printed at the end of every build.
PLACEHOLDERS = {
    "logos/logo-almail-group-white.png": ("Almail Group logo, white (header)",
        "1f2b5af2c800c7194a141d01f38ab2d7412cf891"),
    "logos/logo-azsco-systems.png": ("AZSCO Systems logo, white",
        "9a5d7dc99953e9c9ca9984850f51fb21766ba6a3"),
    "logos/logo-mailarti.png": ("Mailarti logo, white",
        "1fc17ce4996355657eeafc613c0698f250fdce75"),
    "logos/logo-gemellry.png": ("Gemellry logo, white",
        "f9e910f349b3e5c629fd177559aa8a7cf4a6ef0a"),
    "logos/logo-shiplee.png": ("Shiplee logo, white",
        "2b2647856d167c94794f632467faf9ed99a34515"),
    "clients/logo-xcite.png": ("Xcite logo, white",
        "abc17100fb1f7709520f8c0717cce9ab17d1dcd9"),
    "clients/logo-arkan-al-kuwait.png": ("Arkan Al Kuwait Real Estate logo, white",
        "52ca4987926aedcd082086b89738d3247e04ae08"),
    "photos/hero-glass-towers.jpg": ("Hero: looking up at dark glass towers",
        "f36d95f11b4bdb358d34be77844842df62a9d2d9"),
    "photos/why-choose-towers.jpg": ("Why Choose: architecture photo behind the white band",
        "9069ef55c0c07b397179bc19ea4338e05cc904dd"),
    "photos/about-curved-facade.jpg": ("About: modern building, curved glass/steel, from below",
        "f0d09bab23bd5323ed603f045d668db9848edc19"),
    "photos/sectors-glass-facade.jpg": ("Sectors: dark glass facade",
        "f63f1442c4ce45ea3d0cb4cb91d895bfe90087ee"),
    "photos/ceo-high-rise-window.jpg": ("CEO quote: man in a suit at a high-rise window",
        "bce200337bf6bb218c182b6d208c5bdc5f4aec00"),
    "photos/footer-skyscrapers-bw.jpg": ("Footer: black-and-white skyscrapers from below",
        "9cf6452c6e032f17d4816aa39c1e70556a1a9410"),
    "photos/hero-glass-towers-960.jpg": ("960px-wide copy of hero-glass-towers.jpg: replace with a smaller copy of the new photo, or delete",
        "052972cec056fe6cc8d5aa69002f3c5e487b4f75"),
    "photos/why-choose-towers-960.jpg": ("960px-wide copy of why-choose-towers.jpg: replace with a smaller copy of the new photo, or delete",
        "e08d5e548f17ff14254c4bcd99fc38625694ba6d"),
    "photos/about-curved-facade-960.jpg": ("960px-wide copy of about-curved-facade.jpg: replace with a smaller copy of the new photo, or delete",
        "e852c28e384b8c751123d3a16b5938377901a3cb"),
    "photos/sectors-glass-facade-960.jpg": ("960px-wide copy of sectors-glass-facade.jpg: replace with a smaller copy of the new photo, or delete",
        "9d8e639bb0d1e61a2cd204436e65732395128dbc"),
    "photos/ceo-high-rise-window-960.jpg": ("960px-wide copy of ceo-high-rise-window.jpg: replace with a smaller copy of the new photo, or delete",
        "f5f4e0d0d7dd15f54006484ac636f2b8b2a2490d"),
    "photos/footer-skyscrapers-bw-960.jpg": ("960px-wide copy of footer-skyscrapers-bw.jpg: replace with a smaller copy of the new photo, or delete",
        "5a3adf33dd1d94eeec59f1be5791693fb882ea54"),
    "favicon-32.png": ("Favicon, 32px (from the logo)",
        "41731e6927cba293ce5e42764fca7ce67f5de2b3"),
    "favicon-192.png": ("Favicon, 192px (from the logo)",
        "b1306310c18e308cad2062806dbe0354adde9c66"),
    "apple-touch-icon.png": ("Apple touch icon, 180px (from the logo)",
        "c07e3f4b165c7cc731dd06e2a4c9f804d283d484"),
    "og-share.jpg": ("Link preview image, 1200x630",
        "353db63d9c6946e4960db92c17049f0c1a3ea357"),
}


def _sha1(rel):
    with open(os.path.join(OUT, IMG, rel), "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def _is_placeholder(rel):
    entry = PLACEHOLDERS.get(rel)
    return (entry is not None and os.path.exists(os.path.join(OUT, IMG, rel))
            and _sha1(rel) == entry[1])


def placeholders_remaining():
    """(rel, label) for every placeholder still in place. A -960 copy is only
    listed once its full-size photo has been replaced, since it is then unused
    and should be replaced or deleted too."""
    left = []
    for rel, (label, _) in PLACEHOLDERS.items():
        if not _is_placeholder(rel):
            continue
        if rel.endswith("-960.jpg") and _is_placeholder(rel.replace("-960.jpg", ".jpg")):
            continue
        left.append((rel, label))
    return left


# ---------------------------------------------------------------- icons
I = {
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/></svg>',
    "x": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 3h3l-6.6 7.5L21.7 21h-6l-4.7-6.1L5.6 21h-3l7-8L2.6 3h6.1l4.2 5.6zm-1 16h1.7L7.6 4.7H5.8z"/></svg>',
    "close": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    "down": '<svg viewBox="0 0 24 48" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v42"/><path d="m4 36 8 8 8-8"/></svg>',
}

# ============================================================ content
HOME = {
    "title": "Almail Group | Security",
    "desc": ("Almail Group is a Kuwait holding group: real estate, construction and maintenance, "
             "low voltage technology, security, e-commerce, jewelry, smart homes and delivery."),
    "h1": "Almail Group",
    "lead": ("A holding group company that provides a diverse array of products and services, "
             "including real estate services, construction and maintenance, low voltage technologies, "
             "jewelry design, e-commerce, security systems, security guard services, smart home "
             "solutions, and delivery."),
}

WHY = {
    "title": "Why Choose Almail Group?",
    "sub": "Diverse Service Portfolio",
    "text": ("Almail Group offers a diverse range of services including real estate, construction, "
             "technology, e-commerce, security, and smart home solutions. We are committed to "
             "delivering excellence in each domain."),
}

ABOUT = {
    "title": "About Almail Group",
    "sub": "Empowering Through Innovation",
    "text": ("Almail Group is dedicated to empowering individuals and businesses through innovative "
             "solutions. We are committed to delivering top-notch services and creating a positive "
             "impact in every industry we serve."),
}

SUBSIDIARIES = [
    ("AZSCO Systems", "logos/logo-azsco-systems.png"),
    ("Bizarri", "logos/logo-bizarri.png"),
    ("AZSCO Security", "logos/logo-azsco-security.png"),
    ("Mailarti", "logos/logo-mailarti.png"),
    ("Netlet", "logos/logo-netlet.png"),
    ("Gemellry", "logos/logo-gemellry.png"),
    ("Shiplee", "logos/logo-shiplee.png"),
]

SECTORS_INTRO = ("At Almail Group, we bring unparalleled expertise to every project we undertake. "
                 "Our team is proficient in various domains, ensuring exceptional outcomes for our clients.")

SECTORS = ["Security", "Real Estate", "Maintenance", "Smart Solutions",
           "E-Commerce", "Delivery Services", "Jewelry", "Fin-tech"]

PARTNERS = [
    ("Motorola", "partners/logo-motorola.png"),
    ("Ajax", "partners/logo-ajax.png"),
    ("Rasilient", "partners/logo-rasilient.png"),
    ("Avigilon", "partners/logo-avigilon.png"),
    ("Teltonika", "partners/logo-teltonika.png"),
    ("Inrico", "partners/logo-inrico.png"),
    ("Hikvision", "partners/logo-hikvision.png"),
    ("Pelco", "partners/logo-pelco.png"),
]

# Add a dict here to add a slide; the dots and rotation appear on their own.
QUOTES = [
    {"quote": "Our Client Commitment is Beyond Success & Profit.",
     "name": "Dr. Abdulaziz Almail", "role": "Group CEO"},
]

CLIENTS = [
    ("Sayed Hamid Behbehani & Sons", "clients/logo-sayed-hamid-behbehani-sons.png"),
    ("Ream", "clients/logo-ream.png"),
    ("Ewan Complex", "clients/logo-ewan-complex.png"),
    ("Millennium Hotels", "clients/logo-millennium-hotels.png"),
    ("Sahara", "clients/logo-sahara.png"),
    ("Radisson", "clients/logo-radisson.png"),
    ("Alnasser", "clients/logo-alnasser.png"),
    ("NBTC", "clients/logo-nbtc.png"),
    ("National Investments Company", "clients/logo-national-investments-company.png"),
    ("Al Asima", "clients/logo-al-asima.png"),
    ("Massaleh Real Estate", "clients/logo-massaleh-real-estate.png"),
    ("Al-Ahleia Switchgear", "clients/logo-al-ahleia-switchgear.png"),
    ("Awtad", "clients/logo-awtad.png"),
    ("National Contracting Co.", "clients/logo-national-contracting-co.png"),
    ("Alghanim Industries", "clients/logo-alghanim-industries.png"),
    ("Xcite", "clients/logo-xcite.png"),
    ("Wafra", "clients/logo-wafra.png"),
    ("Kuwait Ports Authority", "clients/logo-kuwait-ports-authority.png"),
    ("Ministry of Electricity & Water", "clients/logo-ministry-of-electricity-water.png"),
    ("The Regency", "clients/logo-the-regency.png"),
    ("Arkan Al Kuwait Real Estate", "clients/logo-arkan-al-kuwait.png"),
]

# Pages that exist so the navigation works but have no content yet. They are
# kept out of search results (noindex) and the sitemap until `stub` is False.
STUBS = {
    "almail-group-world.html": {"title": "Almail Group World", "stub": True},
    "our-sectors.html": {"title": "Our Sectors", "stub": True},
    "news.html": {"title": "News", "stub": True},
    "careers.html": {"title": "Careers", "stub": True},
    "contact.html": {"title": "Contact", "stub": False},
}

# ============================================================ templates
FONTS = ("https://fonts.googleapis.com/css2?family=Montserrat:wght@600"
         "&family=Questrial&display=swap")


def head(fname, title, desc, noindex=False, preload=""):
    url = SITE_URL + path_for(fname)
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#000000">
{robots}<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_URL}/{IMG}/og-share.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="/{IMG}/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/{IMG}/favicon-192.png">
<link rel="apple-touch-icon" href="/{IMG}/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{preload}<link rel="stylesheet" href="{FONTS}" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="{FONTS}"></noscript>
<link rel="stylesheet" href="/assets/css/style.css">
<script>document.documentElement.classList.add('js')</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
'''


def nav_items(current, cls):
    out = []
    for label, fname in NAV:
        here = ' aria-current="page"' if fname == current else ""
        out.append(f'<li><a class="{cls}" href="{link(fname)}"{here}>{e(label)}</a></li>')
    return "\n        ".join(out)


def header(current):
    logo = img("logos/logo-almail-group-white.png", "Almail Group", "brand-logo", lazy=False)
    logo_first = img("logos/logo-almail-group-white.png", "Almail Group", "brand-logo", priority=True)
    return f'''
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/">{logo_first}</a>
    <nav class="nav" aria-label="Main">
      <ul>
        {nav_items(current, "nav-link")}
      </ul>
    </nav>
    <button class="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-nav"><span></span></button>
  </div>
</header>

<div class="backdrop" aria-hidden="true"></div>
<nav class="mobile-nav" id="mobile-nav" aria-label="Main">
  <div class="mobile-nav-head">
    <a class="brand" href="/">{logo}</a>
    <button class="close" type="button" aria-label="Close menu">{I["close"]}</button>
  </div>
  <ul>
        {nav_items(current, "m-link")}
  </ul>
</nav>
'''


def social_link(url, label, icon):
    href = url or "#"
    ext = ' target="_blank" rel="noopener noreferrer"' if url else ""
    return f'<li><a href="{href}"{ext} aria-label="{label}">{I[icon]}</a></li>'


def footer():
    hours = "<br>\n          ".join(f"{e(day)}: {e(time)}" for day, time in HOURS)
    address = "<br>\n          ".join(e(line) for line in ADDRESS)
    return f'''
<footer class="site-footer">
  <div class="footer-photo">{img("photos/footer-skyscrapers-bw.jpg", "", sizes="(max-width: 900px) 100vw, 50vw")}</div>
  <div class="footer-panel">
    <h2 class="footer-title">{SITE_NAME}</h2>
    <div class="footer-grid">
      <section>
        <h3>Contact</h3>
        <p><a href="tel:{PHONE_HREF}">{e(PHONE)}</a><br>
          <a href="mailto:{EMAIL_HREF}">{e(EMAIL)}</a></p>
      </section>
      <section>
        <h3>Address</h3>
        <address>{address}</address>
      </section>
      <section>
        <h3>Opening Hours</h3>
        <p>{hours}</p>
      </section>
      <section>
        <h3>Social</h3>
        <ul class="social">
          {social_link(INSTAGRAM_URL, "Almail Group on Instagram", "instagram")}
          {social_link(X_URL, "Almail Group on X", "x")}
        </ul>
      </section>
    </div>
  </div>
</footer>
<script src="/assets/js/main.js" defer></script>
</body>
</html>
'''


PAGES = {}


def page(fname, title, desc, body, noindex=False, preload=""):
    PAGES[fname] = (head(fname, title, desc, noindex, preload) + header(fname)
                    + f'<main id="main">\n{body}\n</main>\n' + footer())


def logo_list(items, cls, label):
    lis = "\n".join(
        f'      <li class="reveal" data-delay="{(n % 5) * 70}">{img(path, name)}</li>'
        for n, (name, path) in enumerate(items))
    return f'    <ul class="{cls}" aria-label="{e(label)}">\n{lis}\n    </ul>'


def hero_preload(photo):
    """The hero photo is the largest thing on first paint; start fetching it
    with the HTML instead of waiting for the parser to reach the <img>."""
    rel = "photos/" + photo
    ss = srcset(rel)
    responsive = f' imagesrcset="{ss}" imagesizes="100vw"' if ss else ""
    return f'<link rel="preload" as="image" href="/{IMG}/{rel}"{responsive} fetchpriority="high">\n'


# ============================================================ pages
HERO_PHOTO = "hero-glass-towers.jpg"


def build_home():
    subs = logo_list(SUBSIDIARIES, "sub-logos", "Almail Group companies")
    sectors = "\n".join(
        f'      <li class="reveal" data-delay="{(n % 2) * 90}"><a class="sector-link" href="{link("our-sectors.html")}">{e(s)}</a></li>'
        for n, s in enumerate(SECTORS))
    partners = logo_list(PARTNERS, "logo-grid logo-grid--partners", "Our partners")
    clients = logo_list(CLIENTS, "logo-grid logo-grid--clients", "Our clients")
    slides = "\n".join(
        f'''      <div class="quote-slide{" is-active" if n == 0 else ""}" role="group" aria-roledescription="slide" aria-label="{n + 1} of {len(QUOTES)}"{"" if n == 0 else " hidden"}>
        <figure>
          <blockquote><p>&ldquo;{e(q["quote"])}&rdquo;</p></blockquote>
          <figcaption><span class="quote-name">{e(q["name"])}</span><span class="quote-role">{e(q["role"])}</span></figcaption>
        </figure>
      </div>''' for n, q in enumerate(QUOTES))
    current = ' aria-current="true"'
    dots = "\n".join(
        f'      <button class="quote-dot" type="button" aria-label="Show quote {n + 1}"{current if n == 0 else ""}></button>'
        for n in range(len(QUOTES)))

    body = f'''
<section class="hero has-bg">
  {backdrop(HERO_PHOTO, priority=True)}
  <div class="wrap hero-inner">
    <h1 class="hero-title">{e(HOME["h1"])}</h1>
    <p class="hero-lead">{e(HOME["lead"])}</p>
  </div>
  <a class="scroll-cue" href="#why" aria-label="Scroll to the next section">{I["down"]}</a>
</section>

<section class="why has-bg" id="why" aria-labelledby="why-title">
  {backdrop("why-choose-towers.jpg")}
  <div class="wrap">
    <div class="why-band reveal">
      <h2 id="why-title">{e(WHY["title"])}</h2>
      <h3>{e(WHY["sub"])}</h3>
      <p>{e(WHY["text"])}</p>
    </div>
  </div>
</section>

<section class="about has-bg" aria-labelledby="about-title">
  {backdrop("about-curved-facade.jpg")}
  <div class="wrap">
    <div class="section-head reveal">
      <h2 id="about-title">{e(ABOUT["title"])}</h2>
      <p class="subtitle">{e(ABOUT["sub"])}</p>
    </div>
    <div class="about-grid">
{subs}
      <p class="about-text reveal">{e(ABOUT["text"])}</p>
    </div>
  </div>
</section>

<section class="sectors has-bg" aria-labelledby="sectors-title">
  {backdrop("sectors-glass-facade.jpg")}
  <div class="wrap">
    <div class="sectors-head reveal">
      <h2 id="sectors-title">Sectors</h2>
      <p>{e(SECTORS_INTRO)}</p>
    </div>
    <ul class="sector-list">
{sectors}
    </ul>
  </div>
</section>

<section class="partners" aria-labelledby="partners-title">
  <div class="wrap">
    <h2 id="partners-title" class="reveal">Our Partners</h2>
{partners}
  </div>
</section>

<section class="quote has-bg" aria-roledescription="carousel" aria-label="Leadership quotes">
  {backdrop("ceo-high-rise-window.jpg")}
  <div class="wrap">
    <div class="quote-track reveal" aria-live="polite">
{slides}
    </div>
    <div class="quote-dots" role="group" aria-label="Choose a quote">
{dots}
    </div>
  </div>
</section>

<section class="clients" aria-labelledby="clients-title">
  <div class="clients-head">
    <div class="wrap">
      <h2 id="clients-title" class="reveal">Our Clients</h2>
      <span class="divider" aria-hidden="true"></span>
    </div>
  </div>
  <div class="clients-body">
    <div class="wrap">
{clients}
    </div>
  </div>
</section>
'''
    page("index.html", HOME["title"], HOME["desc"], body, preload=hero_preload(HERO_PHOTO))


def page_hero(title, lead=""):
    lead_html = f'\n    <p class="page-lead">{lead}</p>' if lead else ""
    return f'''
<section class="page-hero has-bg">
  {backdrop(HERO_PHOTO, priority=True)}
  <div class="wrap">
    <h1>{e(title)}</h1>{lead_html}
  </div>
</section>
'''


def coming_soon():
    return f'''    <p class="stub-note">This page is coming soon.</p>
    <p>In the meantime, call us on <a href="tel:{PHONE_HREF}">{e(PHONE)}</a> or email
      <a href="mailto:{EMAIL_HREF}">{e(EMAIL)}</a>.</p>'''


def stub_section(inner):
    return f'''
<section class="stub">
  <div class="wrap">
{inner}
  </div>
</section>
'''


def build_stubs():
    for fname, meta in STUBS.items():
        title = meta["title"]
        desc = f"{title} — {SITE_NAME}."
        if fname == "contact.html":
            hours = "<br>".join(f"{e(day)}: {e(time)}" for day, time in HOURS)
            address = "<br>".join(e(line) for line in ADDRESS)
            body = page_hero(title) + f'''
<section class="stub">
  <div class="wrap contact-grid">
    <div>
      <h2>Call or email</h2>
      <p><a href="tel:{PHONE_HREF}">{e(PHONE)}</a><br><a href="mailto:{EMAIL_HREF}">{e(EMAIL)}</a></p>
    </div>
    <div>
      <h2>Visit</h2>
      <address>{address}</address>
    </div>
    <div>
      <h2>Opening hours</h2>
      <p>{hours}</p>
    </div>
  </div>
</section>
'''
            desc = (f"Contact {SITE_NAME}: {PHONE}, {EMAIL}. "
                    "Kuwait Building Tower, Floor 27, Fahad Alsalem Street, Qibla City, Kuwait.")
        elif fname == "our-sectors.html":
            items = "\n".join(f'      <li>{e(s)}</li>' for s in SECTORS)
            body = page_hero(title) + stub_section(
                f'    <ul class="stub-sectors">\n{items}\n    </ul>\n' + coming_soon())
        else:
            body = page_hero(title) + stub_section(coming_soon())
        page(fname, f"{title} | {SITE_NAME}", desc, body,
             noindex=meta["stub"], preload=hero_preload(HERO_PHOTO))


def build_404():
    body = page_hero("Page Not Found", "The page you are looking for has moved or no longer exists.") + \
        stub_section('    <p><a class="text-link" href="/">Back to the home page</a></p>')
    page("404.html", f"Page Not Found | {SITE_NAME}",
         "The page you requested could not be found.", body, noindex=True,
         preload=hero_preload(HERO_PHOTO))


# ============================================================ write
def write_sitemap():
    """Only pages with real content: stubs are noindex until they are filled."""
    today = datetime.date.today().isoformat()
    urls = ["index.html"] + [f for f, m in STUBS.items() if not m["stub"]]
    rows = [f"  <url>\n    <loc>{SITE_URL + path_for(f)}</loc>\n    <lastmod>{today}</lastmod>\n  </url>"
            for f in urls]
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)
    return len(rows)


if __name__ == "__main__":
    build_home()
    build_stubs()
    build_404()

    for fname, doc in PAGES.items():
        out_path = out_file_for(fname)
        full = os.path.join(OUT, out_path)
        os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(doc)
        print("wrote", out_path, len(doc), "bytes")

    print("wrote sitemap.xml with", write_sitemap(), "urls")

    left = placeholders_remaining()
    if left:
        print(f"\n{len(left)} placeholder image(s) still in place (assets/img/...):")
        for rel, label in left:
            print(f"  {rel:40s} {label}")
