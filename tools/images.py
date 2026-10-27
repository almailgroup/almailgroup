#!/usr/bin/env python3
"""Make the lighter copies of the site's images that phones and modern
browsers download instead of the originals.

    pip install Pillow        # 11.3 or later, for AVIF
    python3 tools/images.py   # after adding or replacing any image
    python3 tools/build.py

For each photo in assets/img/photos/ (name.jpg, the original):

    name-960.jpg        960px wide, for phones in browsers without AVIF
    name.avif           full size, about half the bytes of the JPEG
    name-960.avif       960px wide
    name-portrait.avif  a tall slice at full resolution, for phones held
                        upright: a phone only shows a narrow strip of a wide
                        photo, so it gets that strip, sharper and smaller than
                        the whole photo scaled down (photos in PORTRAIT only)
    (placeholder)       the photo 32px wide, kept in the record rather than as
                        a file: the pages show it, blurred, while the photo
                        loads, so a section fades from a hint of its photo to
                        the photo instead of from black

For each logo (logos/, partners/, clients/ *.png): name.webp, lossless, so
it is pixel for pixel the PNG at about two thirds of the size.

tools/derived-images.json records which original each copy was made from (its
SHA-1). The build uses a copy only while it still matches its original, so a
photo replaced without running this shows the new JPEG everywhere rather than
the old picture on phones. Copies that are already up to date are skipped.
"""
import base64
import hashlib
import io
import json
import os
import sys

try:
    from PIL import Image, features
except ImportError:
    sys.exit("Pillow is needed: pip install Pillow")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
IMG = os.path.join(ROOT, "assets", "img")
MANIFEST = os.path.join(ROOT, "tools", "derived-images.json")

SMALL_WIDTH = 960
JPEG_QUALITY = 72
AVIF_QUALITY = 50    # the photos sit under 50-78% black overlays; compared side by side, no worse than the JPEGs
PORTRAIT_RATIO = 9 / 16
PLACEHOLDER_WIDTH = 32

# Photos that fill a tall section on a phone, and where across the photo the
# phone's strip is taken from (0 = left edge, 0.5 = middle). Keep these in step
# with object-position in style.css. Only the photos behind a section or a
# page heading use the strip; the footer's photo is wide on a phone too, so the
# footer itself never does.
PORTRAIT = {
    "hero-glass-towers.jpg": 0.5,
    "why-choose-towers.jpg": 0.22,    # the left tower, as `.why .bg img` in style.css
    "about-curved-facade.jpg": 0.5,
    "sectors-glass-facade.jpg": 0.5,
    "ceo-high-rise-window.jpg": 0.5,
    "footer-skyscrapers-bw.jpg": 0.8,  # behind the Careers heading: the darker right-hand tower
}

LOGO_DIRS = ("logos", "partners", "clients")


def sha1(path):
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def rel(path):
    return os.path.relpath(path, IMG).replace(os.sep, "/")


def photo_copies(name):
    """{copy file name: function(original image) -> image to save} for one photo."""
    stem = os.path.splitext(name)[0]

    def small(im):
        w, h = im.size
        return im.resize((SMALL_WIDTH, round(h * SMALL_WIDTH / w)), Image.LANCZOS) if w > SMALL_WIDTH else im

    def portrait(im):
        w, h = im.size
        pw = min(w, round(h * PORTRAIT_RATIO))
        x0 = round((w - pw) * PORTRAIT[name])
        return im.crop((x0, 0, x0 + pw, h))

    copies = {
        f"{stem}-960.jpg": small,
        f"{stem}.avif": lambda im: im,
        f"{stem}-960.avif": small,
    }
    def placeholder(im):
        w, h = im.size
        return im.resize((PLACEHOLDER_WIDTH, max(1, round(h * PLACEHOLDER_WIDTH / w))), Image.LANCZOS)

    if name in PORTRAIT:
        copies[f"{stem}-portrait.avif"] = portrait
    copies[f"{stem}.placeholder"] = placeholder
    return copies


def save(im, path):
    if path.endswith(".jpg"):
        im.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    elif path.endswith(".avif"):
        im.save(path, "AVIF", quality=AVIF_QUALITY, speed=4)
    elif path.endswith(".webp"):
        im.save(path, "WEBP", lossless=True, method=6)


def main():
    if not features.check("avif"):
        sys.exit("This Pillow cannot write AVIF: pip install --upgrade Pillow")
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except FileNotFoundError:
        manifest = {}

    jobs = []   # (original path, copy path, make)
    photos = os.path.join(IMG, "photos")
    for name in sorted(os.listdir(photos)):
        if not name.endswith(".jpg") or name.endswith("-960.jpg"):
            continue
        for copy, make in photo_copies(name).items():
            jobs.append((os.path.join(photos, name), os.path.join(photos, copy), make))
    for d in LOGO_DIRS:
        folder = os.path.join(IMG, d)
        for name in sorted(os.listdir(folder)):
            if name.endswith(".png"):
                src = os.path.join(folder, name)
                jobs.append((src, os.path.splitext(src)[0] + ".webp", lambda im: im))

    made = kept = 0
    wanted = set()
    for src, dst, make in jobs:
        key = rel(dst)
        wanted.add(key)
        digest = sha1(src)
        entry = manifest.get(key)
        inline = dst.endswith(".placeholder")     # kept in the record, not as a file
        if entry and entry["sha1"] == digest and entry["from"] == rel(src) and (inline or os.path.exists(dst)):
            kept += 1
            continue
        with Image.open(src) as im:
            im.load()
            # logos keep their transparency; photos are plain RGB
            out = make(im.convert("RGBA") if dst.endswith(".webp") else im.convert("RGB"))
        manifest[key] = {"from": rel(src), "sha1": digest, "width": out.width, "height": out.height}
        if inline:
            buf = io.BytesIO()
            out.save(buf, "WEBP", quality=40, method=6)
            manifest[key]["data"] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
            # where across the photo a narrow screen looks, for the page to
            # position the placeholder as the photo is positioned
            manifest[key]["focus"] = PORTRAIT.get(os.path.basename(src), 0.5)
            size = f"{buf.tell()} bytes"
        else:
            save(out, dst)
            size = f"{os.path.getsize(dst) // 1024} KB"
        made += 1
        print(f"made {key:48s} {out.width}x{out.height}  {size}")

    # forget copies of originals that no longer exist
    for key in sorted(set(manifest) - wanted):
        del manifest[key]
        print(f"dropped {key} from the record (its original is gone; delete the file if it is still there)")

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(manifest.items())), fh, indent=2)
        fh.write("\n")
    print(f"{made} made, {kept} already up to date")


if __name__ == "__main__":
    main()
