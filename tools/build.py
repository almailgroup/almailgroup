#!/usr/bin/env python3
"""Static builder for the Almail Group website.

Writes every page as plain HTML into the repository root, each in its own
directory (contact/index.html, news/index.html, ...) so addresses are clean:
/contact/, not /contact.html. Stdlib only -- nothing to install.

    python3 tools/build.py

The site is in English and Arabic. English is at the root (/contact/) and
Arabic under /ar/ (/ar/contact/), right to left. Both come from the same
templates: every visible string below is an ("English", "Arabic") pair, so
the two can't drift apart, and a string that is the same in both (a brand
name, a number) is written once.

The lighter image copies (AVIF photos, WebP logos, phone crops) come from
tools/images.py, which needs Pillow; run it first after changing an image.
"""
import datetime
import hashlib
import html
import json
import os
import re
from urllib.parse import quote as urlquote, urlparse

# Output to the repository root (this script lives in <repo>/tools).
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

SITE_URL = "https://www.almailgroup.com"

LANGS = ("en", "ar")


def t(value, lang):
    """The text for one language: a pair gives its English or Arabic half,
    anything else is the same in both."""
    if isinstance(value, tuple):
        return value[0] if lang == "en" else value[1]
    return value


SITE_NAME = ("Almail Group", "مجموعة الميل")

# ---------------------------------------------------------------- contact
PHONE = "+965 - 1808606"
PHONE_HREF = "+9651808606"
EMAIL = "Info@Almailgroup.com"
EMAIL_HREF = "info@almailgroup.com"
ADDRESS = (["Kuwait Building Tower, Floor 27,", "Fahad Alsalem Street,", "Qibla City - Kuwait."],
           ["برج مبنى الكويت، الدور 27،", "شارع فهد السالم،", "القبلة - الكويت."])
# The top bar's one-line address, and the shorter form it falls back to on a
# medium screen. The address opens Google Maps; paste the office's own share
# link here (Maps -> Share -> Copy link) to land on the pin exactly.
ADDRESS_LINE = ("Floor 27, Kuwait Building Tower, Fahad Alsalem St., Qibla, Kuwait",
                "الدور 27، برج مبنى الكويت، شارع فهد السالم، القبلة، الكويت")
ADDRESS_SHORT = ("Kuwait Building Tower, Qibla", "برج مبنى الكويت، القبلة")
MAPS_URL = ("https://www.google.com/maps/search/?api=1&query="
            "Kuwait+Building+Tower%2C+Fahad+Al+Salem+Street%2C+Qibla%2C+Kuwait")
HOURS = [(("Sunday - Thursday", "الأحد - الخميس"), ("8am - 5pm", "8 صباحاً - 5 مساءً")),
         (("Friday", "الجمعة"), ("Closed", "مغلق")),
         (("Saturday", "السبت"), ("Closed", "مغلق"))]

# Paste the profile URLs here and rebuild. Left empty, the icons still show
# but link nowhere ("#").
INSTAGRAM_URL = ""
X_URL = ""

# ---------------------------------------------------------------- routes
# Every page lives in its own directory so the address bar never shows
# ".html"; the home page is the bare site root, and /ar/ for Arabic.
ROUTES = {
    "index.html": "",
    "almail-group-world.html": "almail-group-world",
    "our-sectors.html": "our-sectors",
    "news.html": "news",
    "careers.html": "careers",
    "contact.html": "contact",
}

NAV = [
    (("Home", "الرئيسية"), "index.html"),
    (("Almail Group World", "عالم مجموعة الميل"), "almail-group-world.html"),
    (("Our Sectors", "قطاعاتنا"), "our-sectors.html"),
    (("News", "الأخبار"), "news.html"),
    (("Careers", "الوظائف"), "careers.html"),
    (("Contact", "اتصل بنا"), "contact.html"),
]


def path_for(lang, fname):
    """Root-relative clean URL for a page: '/', '/contact/', '/ar/contact/'."""
    if fname == "404.html":
        return "/404.html"
    slug = ROUTES[fname]
    prefix = "" if lang == "en" else f"/{lang}"
    return f"{prefix}/" if slug == "" else f"{prefix}/{slug}/"


def out_file_for(lang, fname):
    """File the page is physically written to, relative to OUT."""
    if fname == "404.html":
        return "404.html"
    slug = ROUTES[fname]
    rel = "index.html" if slug == "" else f"{slug}/index.html"
    return rel if lang == "en" else f"{lang}/{rel}"


def link(lang, spec):
    """'contact.html' or 'our-sectors.html#security' -> clean URL in that language."""
    fname, _, anchor = spec.partition("#")
    return path_for(lang, fname) + (f"#{anchor}" if anchor else "")


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


_VERSIONS = {}


def asset_url(path):
    """Root-relative address of a file in the repository, with a version taken
    from its contents ('assets/css/style.css' -> '/assets/css/style.css?v=…').

    GitHub Pages lets a browser keep a file for ten minutes under the same
    address, so a page could be drawn with a stylesheet or a photo from before
    the last update: new markup under old styles. A file that changes gets a
    new address, so nothing old can stand in for it."""
    if path not in _VERSIONS:
        with open(os.path.join(OUT, path), "rb") as fh:
            _VERSIONS[path] = hashlib.sha1(fh.read()).hexdigest()[:10]
    return f"/{path}?v={_VERSIONS[path]}"


# Copies made by tools/images.py, each with the SHA-1 of the original it was
# made from. A copy is only used while it still matches its original.
try:
    with open(os.path.join(OUT, "tools", "derived-images.json"), encoding="utf-8") as _fh:
        DERIVED = json.load(_fh)
except FileNotFoundError:
    DERIVED = {}

_STALE = set()


def fresh(copy):
    """True when `copy` (relative to assets/img) exists and was made from the
    current version of its original. A stale copy is noted for the end of the
    build rather than shown, so a replaced photo never reappears as the old one."""
    entry = DERIVED.get(copy)
    if not entry or not os.path.exists(os.path.join(OUT, IMG, copy)):
        return False
    if _sha1(entry["from"]) != entry["sha1"]:
        _STALE.add(entry["from"])
        return False
    return True


def small_version(rel):
    """'photos/hero.jpg' -> 'photos/hero-960.jpg' for phones, when that copy
    exists and is up to date (a hand-made copy tools/images.py did not record
    is trusted as it is)."""
    stem, ext = os.path.splitext(rel)
    small = f"{stem}-960{ext}"
    if not os.path.exists(os.path.join(OUT, IMG, small)):
        return None
    if small in DERIVED and not fresh(small):
        return None
    return small


def srcset(rel):
    small = small_version(rel)
    if not small:
        return ""
    w_small = _image_size(os.path.join(OUT, IMG, small))[0]
    w_full = _image_size(os.path.join(OUT, IMG, rel))[0]
    return f"{asset_url(f'{IMG}/{small}')} {w_small}w, {asset_url(f'{IMG}/{rel}')} {w_full}w"


def avif_srcset(rel):
    """The AVIF copies of a photo as a srcset, or "" when they are missing or stale."""
    stem = os.path.splitext(rel)[0]
    parts = [f"{stem}-960.avif", f"{stem}.avif"]
    if not all(fresh(p) for p in parts):
        return ""
    return ", ".join(f"{asset_url(f'{IMG}/{p}')} {DERIVED[p]['width']}w" for p in parts)


# A phone held upright shows only a tall strip of a wide photo, so it is sent
# the portrait copy of that strip.
PORTRAIT_MEDIA = "(max-width: 640px) and (orientation: portrait)"


def portrait_version(rel):
    copy = os.path.splitext(rel)[0] + "-portrait.avif"
    return copy if fresh(copy) else None


def img(rel, alt, cls="", lazy=True, priority=False, sizes=None, onload=None):
    """An <img> with real width/height (no layout shift) and lazy loading by
    default. `rel` is relative to assets/img/. With `sizes`, a -960 copy of
    the file is offered to small screens when there is one."""
    w, h = _image_size(os.path.join(OUT, IMG, rel))
    attrs = [f'src="{asset_url(f"{IMG}/{rel}")}"', f'alt="{e(alt)}"', f'width="{w}"', f'height="{h}"']
    if cls:
        attrs.insert(0, f'class="{cls}"')
    if sizes and srcset(rel):
        attrs += [f'srcset="{srcset(rel)}"', f'sizes="{sizes}"']
    if priority:
        attrs.append('fetchpriority="high"')
    elif lazy:
        attrs.append('loading="lazy"')
    attrs.append('decoding="async"')
    if onload:
        attrs.append(f'onload="{onload}"')
    return "<img " + " ".join(attrs) + ">"


def picture(rel, alt, cls="", lazy=True, priority=False, sizes=None, portrait=False, onload=None):
    """img() inside a <picture> that offers the lighter copies first: for a
    photo (given `sizes`) AVIF, plus the portrait strip to an upright phone
    when `portrait` is set (photos that fill a tall box there); for a logo
    lossless WebP. A browser that takes neither format, or a copy that is
    missing or out of date, gets the original."""
    tag = img(rel, alt, cls, lazy, priority, sizes, onload)
    sources = []
    if sizes:
        portrait = portrait and portrait_version(rel)
        if portrait:
            sources.append(f'<source media="{PORTRAIT_MEDIA}" type="image/avif" '
                           f'srcset="{asset_url(f"{IMG}/{portrait}")}">')
        avif = avif_srcset(rel)
        if avif:
            sources.append(f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">')
    else:
        webp = os.path.splitext(rel)[0] + ".webp"
        if fresh(webp):
            sources.append(f'<source type="image/webp" srcset="{asset_url(f"{IMG}/{webp}")}">')
    if not sources:
        return tag
    return "<picture>" + "".join(sources) + tag + "</picture>"


def placeholder(rel):
    """The photo 32px wide (tools/images.py) as (data: URL, where across the
    photo a narrow screen looks), or None when it is missing or was made from
    an older version of the photo."""
    entry = DERIVED.get(os.path.splitext(rel)[0] + ".placeholder")
    if not entry or _sha1(entry["from"]) != entry["sha1"]:
        return None
    return entry["data"], entry.get("focus", 0.5)


# Set by the photo when it has loaded. An attribute rather than main.js, so a
# photo that loads before the script runs, or a script that fails to load,
# still shows its photo.
PHOTO_LOADED = "this.closest('.photo').classList.add('is-loaded')"


def photo_box(cls, rel, fade=True, **picture_args):
    """A box holding one photo (class `cls`), which shows the photo's blurred
    placeholder at once and the photo over it once it has loaded, faded in
    unless `fade` is off (style.css, "photos that load")."""
    classes = f"{cls} photo" + (" photo-fade" if fade else "")
    style = ""
    hint = placeholder(rel)
    if hint:
        data, focus = hint
        classes += " has-hint"
        style = f' style="--hint:url({data});--focus:{round(focus * 100)}%"'
    return (f'<div class="{classes}"{style} aria-hidden="true">'
            f'{picture(rel, "", onload=PHOTO_LOADED, **picture_args)}</div>')


def backdrop(photo, priority=False, sizes="100vw"):
    """Full-bleed background photo. A real <img> rather than a CSS background,
    so it lazy-loads below the fold and the hero can be fetched early. The
    hero and the page headings are fetched first and drawn as soon as they
    arrive; the photos further down fade in."""
    return photo_box("bg", "photos/" + photo, fade=not priority, lazy=not priority,
                     priority=priority, sizes=sizes, portrait=True)


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
    """(rel, label) for every placeholder still in place."""
    return [(rel, label) for rel, (label, _) in PLACEHOLDERS.items() if _is_placeholder(rel)]


# ---------------------------------------------------------------- icons
I = {
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/></svg>',
    "x": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 3h3l-6.6 7.5L21.7 21h-6l-4.7-6.1L5.6 21h-3l7-8L2.6 3h6.1l4.2 5.6zm-1 16h1.7L7.6 4.7H5.8z"/></svg>',
    "close": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/></svg>',
    "building": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V4.8a.8.8 0 0 1 .8-.8h9.4a.8.8 0 0 1 .8.8V21"/><path d="M15 9h4.2a.8.8 0 0 1 .8.8V21"/><path d="M2.5 21h19"/><path d="M8 8h3M8 12h3M8 16h3"/></svg>',
    "helmet": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 18h19"/><path d="M4.5 18v-2.5a7.5 7.5 0 0 1 15 0V18"/><path d="M10 8.3V5h4v3.3"/><path d="M8 12.5v-2M16 12.5v-2"/></svg>',
    "chip": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="1.5"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="20" r="1.3"/><circle cx="17" cy="20" r="1.3"/><path d="M3 4h2l2.4 11.2a1 1 0 0 0 1 .8h8.9a1 1 0 0 0 1-.8L20 8H6.2"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
    "smarthome": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M9 14.2a4.2 4.2 0 0 1 6 0"/><path d="M10.8 16.6a1.7 1.7 0 0 1 2.4 0"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 6.5h11v10h-11z"/><path d="M13.5 10h4l3.5 3.5v3h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/></svg>',
    "gem": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 3.5h11l3.5 5.5-9 11.5L3 9z"/><path d="M3 9h18"/><path d="m9.5 3.5-1.5 5.5 4 11.5 4-11.5-1.5-5.5"/></svg>',
    "card": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19"/><path d="M6 14.5h4"/></svg>',
    "external": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6"/><path d="M20 4 10.5 13.5"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>',
    "down": '<svg viewBox="0 0 24 48" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v42"/><path d="m4 36 8 8 8-8"/></svg>',
}
I["up"] = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5"/>'
           '<path d="m5 12 7-7 7 7"/></svg>')
I["globe"] = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
              'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
              '<path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18z"/></svg>')

# ============================================================ content
# Every visible string is an ("English", "Arabic") pair.

HOME = {
    "title": ("Almail Group | Security", "مجموعة الميل | الأمن"),
    "desc": ("Almail Group is a Kuwait holding group: real estate, construction and maintenance, "
             "low voltage technology, security, e-commerce, jewelry, smart homes and delivery.",
             "مجموعة الميل مجموعة قابضة في الكويت تعمل في العقارات والإنشاءات والصيانة وتقنيات "
             "التيار المنخفض والأمن والتجارة الإلكترونية والمجوهرات والمنازل الذكية والتوصيل."),
    "h1": SITE_NAME,
    "lead": ("A holding group company that provides a diverse array of products and services, "
             "including real estate services, construction and maintenance, low voltage technologies, "
             "jewelry design, e-commerce, security systems, security guard services, smart home "
             "solutions, and delivery.",
             "شركة قابضة تقدّم باقة متنوعة من المنتجات والخدمات، تشمل الخدمات العقارية، والإنشاءات "
             "والصيانة، وتقنيات التيار المنخفض، وتصميم المجوهرات، والتجارة الإلكترونية، والأنظمة "
             "الأمنية، وخدمات الحراسة الأمنية، وحلول المنازل الذكية، والتوصيل."),
    # (label, page) -- the first is the filled button
    "actions": [(("Explore our sectors", "تعرّف على قطاعاتنا"), "our-sectors.html"),
                (("Contact us", "تواصل معنا"), "contact.html")],
}

WHY = {
    "title": ("Why Choose Almail Group?", "لماذا تختار مجموعة الميل؟"),
    "sub": ("Diverse Service Portfolio", "محفظة خدمات متنوعة"),
    "text": ("Almail Group offers a diverse range of services including real estate, construction, "
             "technology, e-commerce, security, and smart home solutions. We are committed to "
             "delivering excellence in each domain.",
             "تقدّم مجموعة الميل طيفاً متنوعاً من الخدمات يشمل العقارات، والإنشاءات، والتكنولوجيا، "
             "والتجارة الإلكترونية، والأمن، وحلول المنازل الذكية. ونلتزم بتقديم التميّز في كل مجال."),
    # the six areas the paragraph names, drawn beside it
    "areas": [(("Real estate", "العقارات"), "building"), (("Construction", "الإنشاءات"), "helmet"),
              (("Technology", "التكنولوجيا"), "chip"), (("E-commerce", "التجارة الإلكترونية"), "cart"),
              (("Security", "الأمن"), "shield"), (("Smart home", "المنازل الذكية"), "smarthome")],
}

ABOUT = {
    "title": ("About Almail Group", "عن مجموعة الميل"),
    "sub": ("Empowering Through Innovation", "التمكين من خلال الابتكار"),
    "text": ("Almail Group is dedicated to empowering individuals and businesses through innovative "
             "solutions. We are committed to delivering top-notch services and creating a positive "
             "impact in every industry we serve.",
             "تكرّس مجموعة الميل جهودها لتمكين الأفراد والشركات من خلال حلول مبتكرة. ونلتزم بتقديم "
             "خدمات على أعلى مستوى، وبإحداث أثر إيجابي في كل قطاع نخدمه."),
}

# The group's sectors, in order. The English name is also the sector's anchor
# on the Our Sectors page (/our-sectors/#delivery-services), in both languages.
SECTORS = [("Security", "الأمن"), ("Real Estate", "العقارات"), ("Maintenance", "الصيانة"),
           ("Smart Solutions", "الحلول الذكية"), ("E-Commerce", "التجارة الإلكترونية"),
           ("Delivery Services", "خدمات التوصيل"), ("Jewelry", "المجوهرات"),
           ("Fin-tech", "التكنولوجيا المالية")]
SECTOR = {s[0]: s for s in SECTORS}

SECTORS_INTRO = ("At Almail Group, we bring unparalleled expertise to every project we undertake. "
                 "Our team is proficient in various domains, ensuring exceptional outcomes for our clients.",
                 "في مجموعة الميل، نقدّم خبرة لا مثيل لها في كل مشروع نتولّاه. ويتمتع فريقنا بالكفاءة "
                 "في مجالات متعددة، بما يضمن نتائج استثنائية لعملائنا.")

# Our Sectors page: an icon and a description for each sector, keyed by its
# English name. The companies listed under a sector come from COMPANIES.
SECTOR_INFO = {
    "Security": ("shield", (
        "Guarding for buildings and facilities, VIP protection and rapid intervention, security patrols "
        "and a central operations room, alongside the supply and installation of security systems.",
        "حراسة المباني والمنشآت، وحماية الشخصيات والتدخّل السريع، والدوريات الأمنية وغرفة عمليات "
        "مركزية، إلى جانب توريد الأنظمة الأمنية وتركيبها.")),
    "Real Estate": ("building", (
        "Real estate services, including Bizarri Chalet on the lagoon in Al Khiran.",
        "خدمات عقارية، منها شاليه بيزاري على البحيرة في الخيران.")),
    "Maintenance": ("helmet", ("Construction and maintenance services.", "خدمات الإنشاءات والصيانة.")),
    "Smart Solutions": ("smarthome", (
        "Low voltage technology and smart home solutions: video surveillance, access control, intrusion "
        "and fire detection, and the networks that connect them.",
        "تقنيات التيار المنخفض وحلول المنازل الذكية: المراقبة بالفيديو، والتحكم بالدخول، وكشف التسلل "
        "والحريق، والشبكات التي تربط بينها.")),
    "E-Commerce": ("cart", (
        "NetLet, an online marketplace that brings Kuwait's stores together in one cart.",
        "نت‑لت، سوق إلكتروني يجمع متاجر الكويت في سلة واحدة.")),
    "Delivery Services": ("truck", (
        "Delivery, with Shiplee getting orders to customers' doors.",
        "التوصيل، مع Shiplee التي توصل الطلبات إلى أبواب العملاء.")),
    "Jewelry": ("gem", ("Jewelry design, through Gemellry.", "تصميم المجوهرات من خلال Gemellry.")),
    "Fin-tech": ("card", ("Technology for financial services.", "تقنيات للخدمات المالية.")),
}


def slug(text):
    """'Delivery Services' -> 'delivery-services', the anchor for that sector."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# The group's companies, in the order the Almail Group World page shows them.
# `id` is the company's anchor on that page (/almail-group-world/#bizarri),
# `sectors` the (English) names of the sectors it is listed under, `url` its
# own website ("" when it has none to link to). A company with no `text` yet
# shows "More about ... soon"; fill it in when the description is ready.
# Arabic names are the ones the companies use themselves; a brand without one
# keeps its Latin name.
COMPANIES = [
    {"id": "azsco-security", "name": ("AZSCO Security", "أزسكو للأمن"), "logo": "logos/logo-azsco-security.png",
     "field": ("Security services", "خدمات أمنية"), "url": "https://azsco.com", "sectors": ["Security"],
     "text": ("A Kuwait-based security company: facility guarding, VIP protection and rapid "
              "intervention, security patrols and a central operations room, together with "
              "security systems.",
              "شركة أمن كويتية تقدّم حراسة المنشآت، وحماية الشخصيات والتدخّل السريع، والدوريات "
              "الأمنية، وغرفة عمليات مركزية، إلى جانب الأنظمة الأمنية.")},
    {"id": "azsco-systems", "name": ("AZSCO Systems", "أنظمة أزسكو الأمنية"), "logo": "logos/logo-azsco-systems.png",
     "field": ("Security systems", "أنظمة أمنية"), "url": "https://azsco.systems",
     "sectors": ["Security", "Smart Solutions"],
     "text": ("Supplies and installs security systems in Kuwait: video surveillance, intrusion and "
              "fire detection, access control, and the radio and network hardware behind them.",
              "تورّد الأنظمة الأمنية وتركّبها في الكويت: المراقبة بالفيديو، وكشف التسلل والحريق، "
              "والتحكم بالدخول، وأجهزة الاتصال اللاسلكي والشبكات التي تعمل بها.")},
    {"id": "bizarri", "name": ("Bizarri", "بيزاري"), "logo": "logos/logo-bizarri.png",
     "field": ("Real estate", "عقارات"), "url": "https://bizarri.com", "sectors": ["Real Estate"],
     "text": ("Bizarri Chalet, a chalet to book in Al Khiran: seven bedrooms for 14 guests, a heated "
              "pool, seating on the lagoon and a children's play area.",
              "شاليه بيزاري، شاليه للحجز في الخيران: سبع غرف نوم تتسع لـ14 ضيفاً، ومسبح مُدفّأ، "
              "وجلسات على البحيرة، ومنطقة ألعاب للأطفال.")},
    {"id": "netlet", "name": ("NetLet", "نت‑لت"), "logo": "logos/logo-netlet.png",
     "field": ("E-commerce", "تجارة إلكترونية"), "url": "https://netlet.net", "sectors": ["E-Commerce"],
     "text": ("An online marketplace for Kuwait: products from many stores in one cart, delivered to "
              "every governorate, with cash on delivery.",
              "سوق إلكتروني للكويت: منتجات من متاجر عديدة في سلة واحدة، مع التوصيل إلى جميع "
              "المحافظات والدفع عند الاستلام.")},
    {"id": "shiplee", "name": "Shiplee", "logo": "logos/logo-shiplee.png",
     "field": ("Delivery", "توصيل"), "url": "", "sectors": ["Delivery Services"],
     "text": ("The group's delivery company, getting orders to customers' doors.",
              "شركة التوصيل في المجموعة، توصل الطلبات إلى أبواب العملاء.")},
    {"id": "gemellry", "name": "Gemellry", "logo": "logos/logo-gemellry.png",
     "field": ("Jewelry", "مجوهرات"), "url": "", "sectors": ["Jewelry"],
     "text": ("The group's jewelry design business.", "ذراع المجموعة لتصميم المجوهرات.")},
    {"id": "mailarti", "name": "Mailarti", "logo": "logos/logo-mailarti.png",
     "field": "", "url": "", "sectors": [], "text": ""},
]
COMPANY = {c["id"]: c for c in COMPANIES}

# The home page's About row, in the order the live site shows them.
SUBSIDIARIES = [COMPANY[i] for i in ("azsco-systems", "bizarri", "azsco-security", "mailarti",
                                     "netlet", "gemellry", "shiplee")]

# Partner and client logos: (name, image). The name is the logo's alt text
# and stays as the brand writes it.
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
    {"quote": ("Our Client Commitment is Beyond Success & Profit.",
               "التزامنا تجاه عملائنا يتجاوز النجاح والربح."),
     "name": ("Dr. Abdulaziz Almail", "د. عبدالعزيز الميل"),
     "role": ("Group CEO", "الرئيس التنفيذي للمجموعة")},
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

# News, newest first. Add a dict to publish an item: the date (YYYY-MM-DD), a
# title and the text, one paragraph per string, in each language.
NEWS = [
    {"date": "2026-10-26",
     "title": ("Almail Group launches its new website", "مجموعة الميل تطلق موقعها الإلكتروني الجديد"),
     "text": (["Almail Group's new website brings the group together in one place: its companies, the "
               "sectors they work in, its partners and clients, and every way to reach us.",
               "It is in English and Arabic, quick and easy to use on a phone, and every page carries "
               "our phone number, email and address."],
              ["يجمع الموقع الإلكتروني الجديد لمجموعة الميل المجموعةَ في مكان واحد: شركاتها، والقطاعات "
               "التي تعمل فيها، وشركاءها وعملاءها، وكل وسائل التواصل معنا.",
               "والموقع متاح باللغتين العربية والإنجليزية، سريع وسهل الاستخدام على الهاتف، وتحمل كل صفحة "
               "فيه رقم هاتفنا وبريدنا الإلكتروني وعنواننا."])},
]

# Open positions on the Careers page. With none listed, the page says so and
# invites a CV. To list one, add for example:
#   {"title": ("Security Systems Technician", "فني أنظمة أمنية"), "company": "azsco-systems",
#    "location": ("Kuwait City", "مدينة الكويت"), "type": ("Full time", "دوام كامل"),
#    "text": ("What the role involves and who it suits.", "طبيعة الوظيفة ومن تناسب.")},
JOBS = []

# Where applications go (the subject line is filled in for the applicant).
CAREERS_EMAIL = EMAIL_HREF

# The pages behind the navigation: title, the line under it, its meta
# description and the photo behind its heading.
INNER = {
    "almail-group-world.html": {
        "title": ("Almail Group World", "عالم مجموعة الميل"), "photo": "about-curved-facade.jpg",
        "lead": ("The companies of Almail Group, from security and real estate to e-commerce, delivery and jewelry.",
                 "شركات مجموعة الميل، من الأمن والعقارات إلى التجارة الإلكترونية والتوصيل والمجوهرات."),
        "desc": ("The companies of Almail Group: AZSCO Security, AZSCO Systems, Bizarri, NetLet, Shiplee, "
                 "Gemellry and Mailarti.",
                 "شركات مجموعة الميل: أزسكو للأمن، وأنظمة أزسكو الأمنية، وبيزاري، ونت‑لت، وShiplee، "
                 "وGemellry، وMailarti.")},
    "our-sectors.html": {
        "title": ("Our Sectors", "قطاعاتنا"), "photo": "sectors-glass-facade.jpg",
        "lead": ("Eight sectors, from security and smart solutions to e-commerce, delivery and fin-tech.",
                 "ثمانية قطاعات، من الأمن والحلول الذكية إلى التجارة الإلكترونية والتوصيل والتكنولوجيا المالية."),
        "desc": ("Almail Group's sectors: security, real estate, maintenance, smart solutions, e-commerce, "
                 "delivery services, jewelry and fin-tech.",
                 "قطاعات مجموعة الميل: الأمن، والعقارات، والصيانة، والحلول الذكية، والتجارة الإلكترونية، "
                 "وخدمات التوصيل، والمجوهرات، والتكنولوجيا المالية.")},
    "news.html": {
        "title": ("News", "الأخبار"), "photo": "why-choose-towers.jpg",
        "lead": ("News and announcements from Almail Group and its companies.",
                 "أخبار وإعلانات مجموعة الميل وشركاتها."),
        "desc": ("News and announcements from Almail Group, a holding group in Kuwait.",
                 "أخبار وإعلانات مجموعة الميل، المجموعة القابضة في الكويت.")},
    "careers.html": {
        "title": ("Careers", "الوظائف"), "photo": "footer-skyscrapers-bw.jpg",
        "lead": ("Build your career with Almail Group and its companies.",
                 "ابنِ مسيرتك المهنية مع مجموعة الميل وشركاتها."),
        "desc": ("Careers at Almail Group and its companies in Kuwait: open positions and how to apply.",
                 "الوظائف في مجموعة الميل وشركاتها في الكويت: الشواغر المتاحة وطريقة التقديم.")},
    "contact.html": {
        "title": ("Contact", "اتصل بنا"), "photo": "hero-glass-towers.jpg",
        "lead": ("Call, email or visit us. We're open Sunday to Thursday, 8am to 5pm.",
                 "اتصل بنا أو راسلنا أو زُرنا. نستقبلكم من الأحد إلى الخميس، من 8 صباحاً حتى 5 مساءً."),
        "desc": (f"Contact Almail Group: {PHONE}, {EMAIL}. "
                 "Kuwait Building Tower, Floor 27, Fahad Alsalem Street, Qibla City, Kuwait.",
                 f"تواصل مع مجموعة الميل: {PHONE}، {EMAIL}. "
                 "برج مبنى الكويت، الدور 27، شارع فهد السالم، القبلة، الكويت.")},
}

# Words the templates use, in both languages.
UI = {
    "skip": ("Skip to content", "تخطَّ إلى المحتوى"),
    "main_nav": ("Main", "القائمة الرئيسية"),
    "open_menu": ("Open menu", "فتح القائمة"),
    "close_menu": ("Close menu", "إغلاق القائمة"),
    "home": ("Almail Group, home", "مجموعة الميل، الصفحة الرئيسية"),
    "call_label": ("Call Almail Group on", "اتصل بمجموعة الميل على"),
    "call": ("Call", "اتصل على"),
    "instagram": ("Almail Group on Instagram", "مجموعة الميل على إنستغرام"),
    "x": ("Almail Group on X", "مجموعة الميل على إكس"),
    "contact": ("Contact", "تواصل"),
    "address": ("Address", "العنوان"),
    "hours": ("Opening Hours", "ساعات العمل"),
    "social": ("Social", "تابعنا"),
    "rights": ("All rights reserved.", "جميع الحقوق محفوظة."),
    "to_top": ("Back to top", "العودة إلى الأعلى"),
    "footer_nav": ("Site pages", "صفحات الموقع"),
    "scroll": ("Scroll to the next section", "الانتقال إلى القسم التالي"),
    "areas": ("Areas we work in", "مجالات عملنا"),
    "companies": ("Almail Group companies", "شركات مجموعة الميل"),
    "sectors": ("Sectors", "القطاعات"),
    "partners": ("Our Partners", "شركاؤنا"),
    "clients": ("Our Clients", "عملاؤنا"),
    "quotes": ("Leadership quotes", "كلمات القيادة"),
    "slide": ("slide", "شريحة"),
    "carousel": ("carousel", "عرض متتابع"),
    "of": ("of", "من"),
    "choose_quote": ("Choose a quote", "اختر اقتباساً"),
    "show_quote": ("Show quote", "عرض الاقتباس"),
    "talk": ("Talk to us", "تحدّث إلينا"),
    "talk_text": ("Questions about Almail Group or one of our companies? Call or email us.",
                  "لديك سؤال عن مجموعة الميل أو إحدى شركاتنا؟ اتصل بنا أو راسلنا."),
    "email_us": ("Email us", "راسلنا"),
    "visit": ("Visit", "زيارة"),
    "more_soon": ("More about {name} soon.", "المزيد عن {name} قريباً."),
    "our_companies": ("Our companies", "شركاتنا"),
    "group_companies": ("Group companies", "شركات المجموعة"),
    "no_news": ("There is no news yet. Check back soon.", "لا توجد أخبار بعد. تابعنا قريباً."),
    "media": ("Media enquiries", "الاستفسارات الإعلامية"),
    "media_text": ("For press and media enquiries, email", "للاستفسارات الصحفية والإعلامية، راسلنا على"),
    "follow": ("Follow us for the latest news.", "تابعنا لمعرفة آخر الأخبار."),
    "open_positions": ("Open positions", "الوظائف الشاغرة"),
    "careers_intro": ("Almail Group brings together companies in security, real estate, e-commerce, "
                      "delivery and jewelry. Open roles across the group are listed here.",
                      "تضمّ مجموعة الميل شركات في الأمن والعقارات والتجارة الإلكترونية والتوصيل "
                      "والمجوهرات، ونعرض هنا الوظائف الشاغرة في المجموعة."),
    "no_jobs": ("There are no open positions listed right now. You are still welcome to send us your CV: "
                "tell us the company or the field you would like to work in.",
                "لا توجد وظائف شاغرة معروضة حالياً، ويسعدنا مع ذلك أن تُرسل إلينا سيرتك الذاتية مع ذكر "
                "الشركة أو المجال الذي تودّ العمل فيه."),
    "apply_by_email": ("Apply by email", "قدّم عبر البريد الإلكتروني"),
    "application": ("Application", "طلب توظيف"),
    "job_application": ("Job application", "طلب توظيف"),
    "how_to_apply": ("How to apply", "طريقة التقديم"),
    "step1": ("Choose a field", "اختر مجالاً"),
    "step1_text": ("Find where your experience fits among our sectors.",
                   "حدّد أين تناسب خبرتك بين قطاعاتنا."),
    "step2": ("Prepare your CV", "جهّز سيرتك الذاتية"),
    "step2_text": ("Include your experience, your qualifications, and a phone number and email we can "
                   "reach you on.",
                   "اذكر خبراتك ومؤهلاتك، ورقم هاتف وبريداً إلكترونياً يمكننا التواصل معك من خلالهما."),
    "step3": ("Email it to us", "أرسلها إلينا"),
    "step3_text": ("Send it to {email} with the role or the field in the subject line.",
                   "أرسلها إلى {email} مع ذكر الوظيفة أو المجال في عنوان الرسالة."),
    "email_cv": ("Email your CV", "أرسل سيرتك الذاتية"),
    "where": ("Where you could work", "أين يمكنك أن تعمل"),
    "where_text": ("The companies of Almail Group. Choose one to read what it does.",
                   "شركات مجموعة الميل. اختر إحداها لتتعرّف على عملها."),
    "call_us": ("Call us", "اتصل بنا"),
    "call_now": ("Call now", "اتصل الآن"),
    "send_email": ("Send an email", "أرسل رسالة"),
    "visit_us": ("Visit us", "زُرنا"),
    "directions": ("Get directions", "الاتجاهات"),
    "online": ("Our companies online", "شركاتنا على الإنترنت"),
    "online_text": ("Reach one of our companies directly through its own website.",
                    "تواصل مع أيٍّ من شركاتنا مباشرة عبر موقعها الإلكتروني."),
}

# The language switch names the other language in that language.
LANG_NAME = {"en": "English", "ar": "العربية"}

# Arabic quotes in guillemets, typed opening-first like the text around them
QUOTE_MARKS = {"en": ("&ldquo;", "&rdquo;"), "ar": ("&laquo;", "&raquo;")}

MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

# ============================================================ templates
FONT_FILES = {
    "en": ["assets/fonts/inter-latin.woff2", "assets/fonts/montserrat-latin.woff2"],
    "ar": ["assets/fonts/tajawal-arabic-400.woff2", "assets/fonts/cairo-arabic.woff2"],
}

_CSS = None


def inline_css():
    """The stylesheet, written into each page rather than linked: a phone can
    draw the page from the first response instead of waiting for a second
    request first. Comments and indentation are dropped, and the addresses of
    the files it names get versions like every other asset."""
    global _CSS
    if _CSS is None:
        with open(os.path.join(OUT, "assets", "css", "style.css"), encoding="utf-8") as fh:
            css = re.sub(r"/\*.*?\*/", "", fh.read(), flags=re.S)
        css = "\n".join(line.strip() for line in css.splitlines() if line.strip())
        _CSS = re.sub(r"url\(/(assets/[^)?]+)\)", lambda m: f"url({asset_url(m.group(1))})", css)
    return _CSS


# Chrome and Edge get a page of this site ready in the background, fetched and
# drawn, as soon as a mouse rests on a link to it or a finger lands on one, so
# it opens at once; a browser that can only fetch ahead fetches it, and other
# browsers ignore it.
SPECULATION = ('<script type="speculationrules">'
               '{"prerender": [{"where": {"href_matches": "/*"}, "eagerness": "moderate"}],'
               ' "prefetch": [{"where": {"href_matches": "/*"}, "eagerness": "moderate"}]}'
               '</script>\n')


def structured_data(lang):
    """Who the group is, in the form search engines read (schema.org): name in
    both languages, logo, contact details, address and the group's companies."""
    org = {
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": SITE_NAME[0],
        "alternateName": SITE_NAME[1],
        "url": f"{SITE_URL}/",
        "logo": f"{SITE_URL}/assets/img/icon-512.png",
        "email": EMAIL_HREF,
        "telephone": PHONE_HREF,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Kuwait Building Tower, Floor 27, Fahad Alsalem Street",
            "addressLocality": "Qibla",
            "addressRegion": "Kuwait City",
            "addressCountry": "KW",
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "telephone": PHONE_HREF,
            "email": EMAIL_HREF,
            "areaServed": "KW",
            "availableLanguage": ["English", "Arabic"],
        },
        "subOrganization": [{"@type": "Organization", "name": t(c["name"], "en"), **({"url": c["url"]} if c["url"] else {})}
                            for c in COMPANIES],
    }
    same_as = [u for u in (INSTAGRAM_URL, X_URL) if u]
    if same_as:
        org["sameAs"] = same_as
    site = {
        "@type": "WebSite",
        "@id": f"{SITE_URL}/#website",
        "url": f"{SITE_URL}/",
        "name": t(SITE_NAME, lang),
        "inLanguage": lang,
        "publisher": {"@id": f"{SITE_URL}/#organization"},
    }
    data = json.dumps({"@context": "https://schema.org", "@graph": [org, site]}, ensure_ascii=False)
    return f'<script type="application/ld+json">{data}</script>\n'


def ltr(text, lang):
    """A phone number or an email address: always read left to right, so on an
    Arabic page it is isolated or its '+' and '-' would move about."""
    return e(text) if lang == "en" else f'<bdi dir="ltr">{e(text)}</bdi>'


def other(lang):
    return "ar" if lang == "en" else "en"


def head(lang, fname, title, desc, noindex=False, preload=""):
    url = SITE_URL + path_for(lang, fname)
    fonts = "\n".join(f'<link rel="preload" href="{asset_url(f)}" as="font" type="font/woff2" crossorigin>'
                      for f in FONT_FILES[lang])
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    # each page names its twin in the other language, so search engines show
    # people the one in their language
    alternates = ""
    if fname != "404.html":
        twins = [(code, path_for(code, fname)) for code in LANGS] + [("x-default", path_for("en", fname))]
        alternates = "".join(f'<link rel="alternate" hreflang="{code}" href="{SITE_URL + href}">\n'
                             for code, href in twins)
    locale, alt_locale = ("en_US", "ar_KW") if lang == "en" else ("ar_KW", "en_US")
    direction = ' dir="rtl"' if lang == "ar" else ""
    return f'''<!DOCTYPE html>
<html lang="{lang}"{direction}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#000000">
{robots}<link rel="canonical" href="{url}">
{alternates}<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(t(SITE_NAME, lang))}">
<meta property="og:locale" content="{locale}">
<meta property="og:locale:alternate" content="{alt_locale}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_URL}{asset_url(f"{IMG}/og-share.jpg")}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="{asset_url(f"{IMG}/favicon-32.png")}">
<link rel="icon" type="image/png" sizes="192x192" href="{asset_url(f"{IMG}/favicon-192.png")}">
<link rel="apple-touch-icon" href="{asset_url(f"{IMG}/apple-touch-icon.png")}">
<link rel="manifest" href="{manifest_path(lang)}">
<meta name="apple-mobile-web-app-title" content="{e(t(SITE_NAME, lang))}">
{fonts}
{preload}<style>
{inline_css()}
</style>
<script>document.documentElement.classList.add('js')</script>
{SPECULATION}{structured_data(lang) if fname == "index.html" else ""}</head>
<body>
<a class="skip-link" href="#main">{e(t(UI["skip"], lang))}</a>
'''


def nav_items(lang, current, cls):
    out = []
    for label, fname in NAV:
        here = ' aria-current="page"' if fname == current else ""
        cls_attr = f' class="{cls}"' if cls else ""
        out.append(f'<li><a{cls_attr} href="{link(lang, fname)}"{here}>{e(t(label, lang))}</a></li>')
    return "\n        ".join(out)


def lang_switch(lang, fname, cls):
    """The same page in the other language, named in that language."""
    to = other(lang)
    target = path_for(to, "index.html" if fname == "404.html" else fname)
    return (f'<a class="{cls}" href="{target}" hreflang="{to}" lang="{to}">'
            f'{I["globe"]}<span>{LANG_NAME[to]}</span></a>')


def social_link(url, label, icon):
    href = url or "#"
    ext = ' target="_blank" rel="noopener noreferrer"' if url else ""
    return f'<li><a href="{href}"{ext} aria-label="{label}">{I[icon]}</a></li>'


def socials(lang):
    return (social_link(INSTAGRAM_URL, e(t(UI["instagram"], lang)), "instagram") + "\n        "
            + social_link(X_URL, e(t(UI["x"], lang)), "x"))


def header(lang, current):
    name = t(SITE_NAME, lang)
    logo = picture("logos/logo-almail-group-white.png", name, "brand-logo", lazy=False)
    logo_first = picture("logos/logo-almail-group-white.png", name, "brand-logo", priority=True)
    day, time = HOURS[0]
    home = path_for(lang, "index.html")
    return f'''
<header class="site-header">
  <div class="topbar">
    <div class="wrap topbar-inner">
      <ul class="topbar-contact">
        <li class="tb-address">{I["pin"]}<a href="{MAPS_URL}" target="_blank" rel="noopener noreferrer"><span class="tb-long">{e(t(ADDRESS_LINE, lang))}</span><span class="tb-short">{e(t(ADDRESS_SHORT, lang))}</span></a></li>
        <li>{I["phone"]}<a href="tel:{PHONE_HREF}">{ltr(PHONE, lang)}</a></li>
        <li class="tb-email">{I["mail"]}<a href="mailto:{EMAIL_HREF}">{ltr(EMAIL, lang)}</a></li>
      </ul>
      <div class="topbar-end">
        {lang_switch(lang, current, "lang-link")}
        <ul class="topbar-social">
        {socials(lang)}
        </ul>
      </div>
    </div>
  </div>
  <div class="wrap header-inner">
    <a class="brand" href="{home}">{logo_first}</a>
    <nav class="nav" aria-label="{e(t(UI["main_nav"], lang))}">
      <ul>
        {nav_items(lang, current, "nav-link")}
      </ul>
    </nav>
    {lang_switch(lang, current, "lang-link header-lang")}
    <div class="header-actions">
      <a class="call-btn" href="tel:{PHONE_HREF}" aria-label="{e(t(UI["call_label"], lang))} {e(PHONE)}">{I["phone"]}</a>
      <button class="burger" type="button" aria-label="{e(t(UI["open_menu"], lang))}" aria-expanded="false" aria-controls="mobile-nav"><span></span></button>
    </div>
  </div>
</header>

<div class="backdrop" aria-hidden="true"></div>
<nav class="mobile-nav" id="mobile-nav" aria-label="{e(t(UI["main_nav"], lang))}">
  <div class="mobile-nav-head">
    <a class="brand" href="{home}">{logo}</a>
    <button class="close" type="button" aria-label="{e(t(UI["close_menu"], lang))}">{I["close"]}</button>
  </div>
  <ul>
        {nav_items(lang, current, "m-link")}
  </ul>
  {lang_switch(lang, current, "m-lang")}
  <div class="m-contact">
    <a class="btn btn-primary m-call" href="tel:{PHONE_HREF}">{I["phone"]}<span>{e(t(UI["call"], lang))} {ltr(PHONE, lang)}</span></a>
    <ul class="m-details">
      <li>{I["mail"]}<a href="mailto:{EMAIL_HREF}">{ltr(EMAIL, lang)}</a></li>
      <li>{I["pin"]}<a href="{MAPS_URL}" target="_blank" rel="noopener noreferrer">{e(t(ADDRESS_SHORT, lang))}</a></li>
      <li>{I["clock"]}<span>{e(t(day, lang))}: {e(t(time, lang))}</span></li>
    </ul>
    <ul class="social m-social">
      {socials(lang)}
    </ul>
  </div>
</nav>
'''


def footer(lang, current):
    hours = "<br>\n          ".join(f"{e(t(day, lang))}: {e(t(time, lang))}" for day, time in HOURS)
    address = "<br>\n          ".join(e(line) for line in t(ADDRESS, lang))
    name = t(SITE_NAME, lang)
    return f'''
<footer class="site-footer">
  {photo_box("footer-photo", "photos/footer-skyscrapers-bw.jpg", sizes="(max-width: 900px) 100vw, 42vw")}
  <div class="footer-panel">
    <h2 class="footer-title">{e(name)}</h2>
    <div class="footer-grid">
      <section>
        <h3>{e(t(UI["contact"], lang))}</h3>
        <ul class="footer-contact">
          <li><a href="tel:{PHONE_HREF}">{ltr(PHONE, lang)}</a></li>
          <li><a href="mailto:{EMAIL_HREF}">{ltr(EMAIL, lang)}</a></li>
        </ul>
      </section>
      <section>
        <h3>{e(t(UI["address"], lang))}</h3>
        <address><a href="{MAPS_URL}" target="_blank" rel="noopener noreferrer">{address}</a></address>
      </section>
      <section>
        <h3>{e(t(UI["hours"], lang))}</h3>
        <p>{hours}</p>
      </section>
      <section>
        <h3>{e(t(UI["social"], lang))}</h3>
        <ul class="social">
          {socials(lang)}
        </ul>
      </section>
    </div>
    <nav class="footer-nav" aria-label="{e(t(UI["footer_nav"], lang))}">
      <ul>
        {nav_items(lang, current, "")}
      </ul>
    </nav>
    <p class="footer-legal">&copy; {datetime.date.today().year} {e(name)}. {e(t(UI["rights"], lang))}</p>
  </div>
  <button class="to-top" type="button" aria-label="{e(t(UI["to_top"], lang))}" hidden>{I["up"]}</button>
</footer>
<script src="{asset_url("assets/js/main.js")}" defer></script>
</body>
</html>
'''


PAGES = {}


def page(lang, fname, title, desc, body, noindex=False, preload=""):
    PAGES[(lang, fname)] = (head(lang, fname, title, desc, noindex, preload) + header(lang, fname)
                            + f'<main id="main">\n{body}\n</main>\n' + footer(lang, fname))


def logo_list(items, cls, label):
    lis = "\n".join(
        f'      <li class="reveal" data-delay="{(n % 5) * 50}">{picture(path, name)}</li>'
        for n, (name, path) in enumerate(items))
    return f'    <ul class="{cls}" aria-label="{e(label)}">\n{lis}\n    </ul>'


def company_tiles(lang, companies):
    """Company logos as tiles, each opening its card on Almail Group World."""
    lis = "\n".join(
        f'      <li class="reveal" data-delay="{(n % 4) * 50}"><a href="{link(lang, "almail-group-world.html#" + c["id"])}">'
        f'{picture(c["logo"], t(c["name"], lang))}</a></li>'
        for n, c in enumerate(companies))
    return f'    <ul class="sub-logos" aria-label="{e(t(UI["companies"], lang))}">\n{lis}\n    </ul>'


def hero_preload(photo):
    """The hero photo is the largest thing on first paint; start fetching it
    with the HTML instead of waiting for the parser to reach the <img>. The
    preloads name the same files the <picture> will choose: the portrait strip
    on an upright phone, the AVIF copies elsewhere. A browser without AVIF
    skips them and fetches the JPEG when it reaches the <img>."""
    rel = "photos/" + photo
    avif = avif_srcset(rel)
    if not avif:
        ss = srcset(rel)
        responsive = f' imagesrcset="{ss}" imagesizes="100vw"' if ss else ""
        return f'<link rel="preload" as="image" href="{asset_url(f"{IMG}/{rel}")}"{responsive} fetchpriority="high">\n'
    full = asset_url(f"{IMG}/{os.path.splitext(rel)[0]}.avif")
    portrait = portrait_version(rel)
    media = f' media="not all and {PORTRAIT_MEDIA}"' if portrait else ""
    out = (f'<link rel="preload" as="image" type="image/avif" href="{full}" imagesrcset="{avif}" '
           f'imagesizes="100vw"{media} fetchpriority="high">\n')
    if portrait:
        out += (f'<link rel="preload" as="image" type="image/avif" href="{asset_url(f"{IMG}/{portrait}")}" '
                f'media="{PORTRAIT_MEDIA}" fetchpriority="high">\n')
    return out


# ============================================================ pages
HERO_PHOTO = "hero-glass-towers.jpg"


def build_home(lang):
    sectors = "\n".join(
        f'      <li class="reveal" data-delay="{(n % 2) * 60}"><a class="sector-link" href="{link(lang, "our-sectors.html#" + slug(s[0]))}">'
        f'<span class="sector-num" aria-hidden="true">{n + 1:02d}</span><span class="sector-name">{e(t(s, lang))}</span>'
        f'<span class="sector-arrow">{I["arrow"]}</span></a></li>'
        for n, s in enumerate(SECTORS))
    actions = "\n".join(
        f'      <a class="btn {"btn-primary" if n == 0 else "btn-ghost"}" href="{link(lang, target)}">{e(t(label, lang))}</a>'
        for n, (label, target) in enumerate(HOME["actions"]))
    areas = "\n".join(
        f'          <li><span class="why-icon">{I[icon]}</span>{e(t(label, lang))}</li>' for label, icon in WHY["areas"])
    partners = logo_list(PARTNERS, "logo-grid logo-grid--partners", t(UI["partners"], lang))
    clients = logo_list(CLIENTS, "logo-grid logo-grid--clients", t(UI["clients"], lang))
    of = t(UI["of"], lang)
    slides = "\n".join(
        f'''      <div class="quote-slide{" is-active" if n == 0 else ""}" role="group" aria-roledescription="{e(t(UI["slide"], lang))}" aria-label="{n + 1} {of} {len(QUOTES)}"{"" if n == 0 else " hidden"}>
        <figure>
          <blockquote><p>{QUOTE_MARKS[lang][0]}{e(t(q["quote"], lang))}{QUOTE_MARKS[lang][1]}</p></blockquote>
          <figcaption><span class="quote-name">{e(t(q["name"], lang))}</span><span class="quote-role">{e(t(q["role"], lang))}</span></figcaption>
        </figure>
      </div>''' for n, q in enumerate(QUOTES))
    current = ' aria-current="true"'
    dots = "\n".join(
        f'      <button class="quote-dot" type="button" aria-label="{e(t(UI["show_quote"], lang))} {n + 1}"{current if n == 0 else ""}></button>'
        for n in range(len(QUOTES)))
    # with one quote there is nothing to choose between, so no dots
    dots = (f'    <div class="quote-dots" role="group" aria-label="{e(t(UI["choose_quote"], lang))}">\n{dots}\n    </div>'
            if len(QUOTES) > 1 else "")

    body = f'''
<section class="hero has-bg">
  {backdrop(HERO_PHOTO, priority=True)}
  <div class="wrap hero-inner">
    <h1 class="hero-title">{e(t(HOME["h1"], lang))}</h1>
    <p class="hero-lead">{e(t(HOME["lead"], lang))}</p>
    <div class="hero-actions">
{actions}
    </div>
  </div>
  <a class="scroll-cue" href="#why" aria-label="{e(t(UI["scroll"], lang))}">{I["down"]}</a>
</section>

<section class="why has-bg" id="why" aria-labelledby="why-title">
  {backdrop("why-choose-towers.jpg")}
  <div class="wrap">
    <div class="why-band reveal">
      <h2 id="why-title">{e(t(WHY["title"], lang))}</h2>
      <div class="why-body">
        <div class="why-copy">
          <h3>{e(t(WHY["sub"], lang))}</h3>
          <p>{e(t(WHY["text"], lang))}</p>
        </div>
        <ul class="why-areas" aria-label="{e(t(UI["areas"], lang))}">
{areas}
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="about has-bg" aria-labelledby="about-title">
  {backdrop("about-curved-facade.jpg")}
  <div class="wrap">
    <div class="about-head">
      <div class="section-head reveal">
        <h2 id="about-title">{e(t(ABOUT["title"], lang))}</h2>
        <p class="subtitle">{e(t(ABOUT["sub"], lang))}</p>
      </div>
      <p class="about-text reveal">{e(t(ABOUT["text"], lang))}</p>
    </div>
{company_tiles(lang, SUBSIDIARIES)}
  </div>
</section>

<section class="sectors has-bg" aria-labelledby="sectors-title">
  {backdrop("sectors-glass-facade.jpg")}
  <div class="wrap">
    <div class="sectors-head reveal">
      <h2 id="sectors-title">{e(t(UI["sectors"], lang))}</h2>
      <p>{e(t(SECTORS_INTRO, lang))}</p>
    </div>
    <ul class="sector-list">
{sectors}
    </ul>
  </div>
</section>

<section class="partners" aria-labelledby="partners-title">
  <div class="wrap">
    <h2 id="partners-title" class="reveal">{e(t(UI["partners"], lang))}</h2>
{partners}
  </div>
</section>

<section class="quote has-bg" aria-roledescription="{e(t(UI["carousel"], lang))}" aria-label="{e(t(UI["quotes"], lang))}">
  {backdrop("ceo-high-rise-window.jpg")}
  <div class="wrap">
    <div class="quote-track reveal" aria-live="polite">
{slides}
    </div>
{dots}
  </div>
</section>

<section class="clients" aria-labelledby="clients-title">
  <div class="clients-head">
    <div class="wrap">
      <h2 id="clients-title" class="reveal">{e(t(UI["clients"], lang))}</h2>
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
    page(lang, "index.html", t(HOME["title"], lang), t(HOME["desc"], lang), body,
         preload=hero_preload(HERO_PHOTO))


def page_hero(title, lead, photo):
    return f"""
<section class="page-hero has-bg">
  {backdrop(photo, priority=True)}
  <div class="wrap">
    <h1>{e(title)}</h1>
    <p class="page-lead">{e(lead)}</p>
  </div>
</section>
"""


def inner_page(lang, fname, body):
    meta = INNER[fname]
    title = t(meta['title'], lang)
    page(lang, fname, f'{title} | {t(SITE_NAME, lang)}', t(meta['desc'], lang),
         page_hero(title, t(meta['lead'], lang), meta['photo']) + body,
         preload=hero_preload(meta['photo']))


def cta(lang):
    """The closing band on inner pages: a line and the two quickest ways to reach us."""
    return f"""
<section class="cta-band" aria-labelledby="cta-title">
  <div class="wrap cta-inner">
    <div class="reveal">
      <h2 id="cta-title">{e(t(UI['talk'], lang))}</h2>
      <p>{e(t(UI['talk_text'], lang))}</p>
    </div>
    <div class="cta-actions reveal">
      <a class="btn btn-primary" href="tel:{PHONE_HREF}">{I['phone']}<span>{e(t(UI['call'], lang))} {ltr(PHONE, lang)}</span></a>
      <a class="btn btn-ghost" href="mailto:{EMAIL_HREF}">{I['mail']}<span>{e(t(UI['email_us'], lang))}</span></a>
    </div>
  </div>
</section>
"""


def chips(items, label):
    """A labelled row of links, e.g. a company's sectors: [(text, href)]."""
    if not items:
        return ""
    lis = "".join(f'<li><a class="chip" href="{href}">{e(text)}</a></li>' for text, href in items)
    return f'<p class="chips-label">{e(label)}</p><ul class="chips">{lis}</ul>'


def domain(url):
    return urlparse(url).netloc.removeprefix("www.")


def website_link(lang, c, cls="company-link"):
    return (f'<a class="{cls}" href="{c["url"]}" target="_blank" rel="noopener noreferrer">'
            f'<span>{e(t(UI["visit"], lang))} <bdi>{e(domain(c["url"]))}</bdi></span>{I["external"]}</a>')


def build_world(lang):
    cards = []
    for c in COMPANIES:
        name = t(c['name'], lang)
        field = f'<p class="company-field">{e(t(c["field"], lang))}</p>' if c['field'] else ""
        text = e(t(c['text'], lang)) if c['text'] else e(t(UI['more_soon'], lang).format(name=name))
        sectors = chips([(t(SECTOR[s], lang), link(lang, "our-sectors.html#" + slug(s))) for s in c['sectors']],
                        t(UI['sectors'], lang))
        site = website_link(lang, c) if c['url'] else ""
        cards.append(f"""      <article class="company-card reveal" id="{c['id']}">
        <div class="company-logo">{picture(c['logo'], '')}</div>
        <div class="company-body">
          {field}
          <h3>{e(name)}</h3>
          <p class="company-text">{text}</p>
          {sectors}
          {site}
        </div>
      </article>""")
    body = f"""
<section class="page-section" aria-labelledby="companies-title">
  <div class="wrap">
    <div class="section-head reveal">
      <h2 id="companies-title">{e(t(UI['our_companies'], lang))}</h2>
      <p class="lead-text">{e(t(ABOUT['text'], lang))}</p>
    </div>
    <div class="company-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>
""" + cta(lang)
    inner_page(lang, "almail-group-world.html", body)


def build_sectors(lang):
    cards = []
    for n, s in enumerate(SECTORS):
        icon, text = SECTOR_INFO[s[0]]
        companies = [(t(c['name'], lang), link(lang, "almail-group-world.html#" + c['id']))
                     for c in COMPANIES if s[0] in c['sectors']]
        cards.append(f"""      <article class="sector-card reveal" id="{slug(s[0])}" data-delay="{(n % 2) * 60}">
        <div class="sector-card-top"><span class="icon-badge">{I[icon]}</span><span class="sector-num" aria-hidden="true">{n + 1:02d}</span></div>
        <h2>{e(t(s, lang))}</h2>
        <p class="sector-text">{e(t(text, lang))}</p>
        {chips(companies, t(UI['group_companies'], lang))}
      </article>""")
    body = f"""
<section class="page-section">
  <div class="wrap">
    <p class="lead-text page-intro reveal">{e(t(SECTORS_INTRO, lang))}</p>
    <div class="sector-cards">
{chr(10).join(cards)}
    </div>
  </div>
</section>
""" + cta(lang)
    inner_page(lang, "our-sectors.html", body)


def long_date(iso, lang):
    d = datetime.date.fromisoformat(iso)
    month = d.strftime('%B') if lang == "en" else MONTHS_AR[d.month - 1]
    return f"{d.day} {month} {d.year}"


def build_news(lang):
    if NEWS:
        items = "\n".join(
            f"""      <li><article class="item-card reveal">
        <time class="item-meta" datetime="{n['date']}">{long_date(n['date'], lang)}</time>
        <h2>{e(t(n['title'], lang))}</h2>
        {''.join(f'<p>{e(par)}</p>' for par in t(n['text'], lang))}
      </article></li>""" for n in NEWS)
        listing = f'    <ul class="item-list">\n{items}\n    </ul>'
    else:
        listing = f'    <p class="empty-note reveal">{e(t(UI["no_news"], lang))}</p>'
    social = [(url, e(t(UI[key], lang)), key) for url, key in ((INSTAGRAM_URL, "instagram"), (X_URL, "x")) if url]
    follow = ""
    if social:
        follow = (f'\n      <p>{e(t(UI["follow"], lang))}</p>\n      <ul class="social">'
                  + "".join(social_link(*sl) for sl in social) + "</ul>")
    body = f"""
<section class="page-section">
  <div class="wrap news-layout">
{listing}
    <aside class="side-note reveal" aria-labelledby="media-title">
      <h2 id="media-title">{e(t(UI['media'], lang))}</h2>
      <p>{e(t(UI['media_text'], lang))} <a href="mailto:{EMAIL_HREF}">{ltr(EMAIL, lang)}</a>.</p>{follow}
    </aside>
  </div>
</section>
"""
    inner_page(lang, "news.html", body)


def build_careers(lang):
    apply_href = f"mailto:{CAREERS_EMAIL}?subject={urlquote(t(UI['job_application'], lang))}"
    if JOBS:
        items = []
        for j in JOBS:
            company = t(COMPANY[j['company']]['name'], lang) if j.get('company') in COMPANY else t(j.get('company', ''), lang)
            meta = " · ".join(x for x in (company, t(j.get('location', ''), lang), t(j.get('type', ''), lang)) if x)
            subject = urlquote(f"{t(UI['application'], lang)}: {t(j['title'], lang)}")
            items.append(f"""      <li><article class="item-card reveal">
        <p class="item-meta">{e(meta)}</p>
        <h3>{e(t(j['title'], lang))}</h3>
        <p>{e(t(j['text'], lang))}</p>
        <a class="btn btn-ghost" href="mailto:{CAREERS_EMAIL}?subject={subject}">{e(t(UI['apply_by_email'], lang))}</a>
      </article></li>""")
        jobs = '    <ul class="item-list">\n' + "\n".join(items) + '\n    </ul>'
    else:
        jobs = f'    <p class="empty-note reveal">{e(t(UI["no_jobs"], lang))}</p>'
    fields = "".join(f'<li><span class="chip">{e(t(s, lang))}</span></li>' for s in SECTORS)
    send_to = e(t(UI['step3_text'], lang)).replace("{email}", f'<a href="{apply_href}">{ltr(EMAIL, lang)}</a>')
    body = f"""
<section class="page-section" aria-labelledby="jobs-title">
  <div class="wrap">
    <div class="section-head reveal">
      <h2 id="jobs-title">{e(t(UI['open_positions'], lang))}</h2>
      <p class="lead-text">{e(t(UI['careers_intro'], lang))}</p>
    </div>
{jobs}
  </div>
</section>

<section class="page-section page-section--alt" aria-labelledby="apply-title">
  <div class="wrap">
    <h2 id="apply-title" class="reveal">{e(t(UI['how_to_apply'], lang))}</h2>
    <ol class="steps">
      <li class="reveal">
        <span class="step-num" aria-hidden="true">1</span>
        <h3>{e(t(UI['step1'], lang))}</h3>
        <p>{e(t(UI['step1_text'], lang))}</p>
        <ul class="chips">{fields}</ul>
      </li>
      <li class="reveal" data-delay="60">
        <span class="step-num" aria-hidden="true">2</span>
        <h3>{e(t(UI['step2'], lang))}</h3>
        <p>{e(t(UI['step2_text'], lang))}</p>
      </li>
      <li class="reveal" data-delay="120">
        <span class="step-num" aria-hidden="true">3</span>
        <h3>{e(t(UI['step3'], lang))}</h3>
        <p>{send_to}</p>
        <a class="btn btn-primary" href="{apply_href}">{I['mail']}<span>{e(t(UI['email_cv'], lang))}</span></a>
      </li>
    </ol>
  </div>
</section>

<section class="page-section" aria-labelledby="where-title">
  <div class="wrap">
    <div class="section-head reveal">
      <h2 id="where-title">{e(t(UI['where'], lang))}</h2>
      <p class="lead-text">{e(t(UI['where_text'], lang))}</p>
    </div>
{company_tiles(lang, COMPANIES)}
  </div>
</section>
"""
    inner_page(lang, "careers.html", body)


def build_contact(lang):
    address = "<br>".join(e(line) for line in t(ADDRESS, lang))
    hours = "".join(f"<li><span>{e(t(day, lang))}</span><span>{e(t(time, lang))}</span></li>" for day, time in HOURS)
    online = "\n".join(
        f"""      <li class="reveal" data-delay="{n * 60}">
        <a class="online-card" href="{c['url']}" target="_blank" rel="noopener noreferrer">
          <span class="online-logo">{picture(c['logo'], '')}</span>
          <span class="online-name">{e(t(c['name'], lang))}</span>
          <span class="online-url"><bdi>{e(domain(c['url']))}</bdi>{I['external']}</span>
        </a>
      </li>""" for n, c in enumerate(c for c in COMPANIES if c['url']))
    body = f"""
<section class="page-section">
  <div class="wrap">
    <div class="contact-cards">
      <article class="contact-card reveal">
        <span class="icon-badge">{I['phone']}</span>
        <h2>{e(t(UI['call_us'], lang))}</h2>
        <p><a href="tel:{PHONE_HREF}">{ltr(PHONE, lang)}</a></p>
        <a class="btn btn-primary" href="tel:{PHONE_HREF}">{e(t(UI['call_now'], lang))}</a>
      </article>
      <article class="contact-card reveal" data-delay="50">
        <span class="icon-badge">{I['mail']}</span>
        <h2>{e(t(UI['email_us'], lang))}</h2>
        <p><a href="mailto:{EMAIL_HREF}">{ltr(EMAIL, lang)}</a></p>
        <a class="btn btn-ghost" href="mailto:{EMAIL_HREF}">{e(t(UI['send_email'], lang))}</a>
      </article>
      <article class="contact-card reveal" data-delay="100">
        <span class="icon-badge">{I['pin']}</span>
        <h2>{e(t(UI['visit_us'], lang))}</h2>
        <address>{address}</address>
        <a class="btn btn-ghost" href="{MAPS_URL}" target="_blank" rel="noopener noreferrer">{e(t(UI['directions'], lang))}</a>
      </article>
      <article class="contact-card reveal" data-delay="150">
        <span class="icon-badge">{I['clock']}</span>
        <h2>{e(t(UI['hours'], lang))}</h2>
        <ul class="hours">{hours}</ul>
      </article>
    </div>
  </div>
</section>

<section class="page-section page-section--alt" aria-labelledby="online-title">
  <div class="wrap">
    <div class="section-head reveal">
      <h2 id="online-title">{e(t(UI['online'], lang))}</h2>
      <p class="lead-text">{e(t(UI['online_text'], lang))}</p>
    </div>
    <ul class="online-list">
{online}
    </ul>
  </div>
</section>
"""
    inner_page(lang, "contact.html", body)


def build_404():
    """One not-found page serves both languages (GitHub Pages has one), so it
    offers the way home in each."""
    body = page_hero("Page Not Found", "The page you are looking for has moved or no longer exists.", HERO_PHOTO) + """
<section class="page-section">
  <div class="wrap">
    <p><a class="text-link" href="/">Back to the home page</a></p>
    <p class="not-found-ar" lang="ar" dir="rtl"><a class="text-link" href="/ar/">العودة إلى الصفحة الرئيسية</a></p>
  </div>
</section>
"""
    page("en", "404.html", "Page Not Found | Almail Group",
         "The page you requested could not be found.", body, noindex=True,
         preload=hero_preload(HERO_PHOTO))


# ============================================================ write
def manifest_path(lang):
    return "/manifest.webmanifest" if lang == "en" else f"/{lang}/manifest.webmanifest"


def write_manifests():
    """What a phone uses when someone adds the site to their home screen: the
    name under the icon, the icons, and the page it opens on, per language.
    "minimal-ui" keeps a back button, which a site of pages needs."""
    for lang in LANGS:
        manifest = {
            "name": t(SITE_NAME, lang),
            "short_name": t(SITE_NAME, lang),
            "description": t(HOME["desc"], lang),
            "lang": lang,
            "dir": "rtl" if lang == "ar" else "ltr",
            "start_url": path_for(lang, "index.html"),
            "scope": "/",
            "display": "minimal-ui",
            "background_color": "#000000",
            "theme_color": "#000000",
            "icons": [
                {"src": asset_url(f"{IMG}/favicon-192.png"), "sizes": "192x192", "type": "image/png"},
                {"src": asset_url(f"{IMG}/icon-512.png"), "sizes": "512x512", "type": "image/png"},
                {"src": asset_url(f"{IMG}/icon-maskable-512.png"), "sizes": "512x512", "type": "image/png",
                 "purpose": "maskable"},
            ],
        }
        path = os.path.join(OUT, manifest_path(lang).lstrip("/"))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
            fh.write("\n")


def write_sitemap():
    """Every page in both languages, each naming its twin in the other."""
    today = datetime.date.today().isoformat()
    rows = []
    for lang in LANGS:
        for fname in ROUTES:
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{code}" href="{SITE_URL + path_for(code, fname)}"/>'
                for code in LANGS)
            rows.append(f"  <url>\n    <loc>{SITE_URL + path_for(lang, fname)}</loc>{alts}\n"
                        f"    <lastmod>{today}</lastmod>\n  </url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)
    return len(rows)


if __name__ == "__main__":
    for lang in LANGS:
        build_home(lang)
        build_world(lang)
        build_sectors(lang)
        build_news(lang)
        build_careers(lang)
        build_contact(lang)
    build_404()

    for (lang, fname), doc in PAGES.items():
        out_path = out_file_for(lang, fname)
        full = os.path.join(OUT, out_path)
        os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(doc)
        print("wrote", out_path, len(doc), "bytes")

    print("wrote sitemap.xml with", write_sitemap(), "urls")
    write_manifests()
    print("wrote manifest.webmanifest and ar/manifest.webmanifest")

    if _STALE:
        print(f"\n{len(_STALE)} image(s) changed since tools/images.py last ran, so pages use the original"
              " file for now. Run python3 tools/images.py, then this again:")
        for rel in sorted(_STALE):
            print(f"  {rel}")

    left = placeholders_remaining()
    if left:
        print(f"\n{len(left)} placeholder image(s) still in place (assets/img/...):")
        for rel, label in left:
            print(f"  {rel:40s} {label}")
