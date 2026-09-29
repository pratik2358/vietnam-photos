"""Build the site: resize photos/ into img/ and write index.html from LAYOUT.

Usage: python3 build.py
Each chapter reads from its own folder in photos/ (photos/hanoi, photos/sapa, ...).
Photos are referenced by file number (e.g. "9553" -> DSCF9553.jpg).
A photo in a chapter's folder that LAYOUT doesn't mention is added to the end of
that chapter, so new photos show up without editing LAYOUT.
Row types:
  full    one photo, edge to edge
  center  one photo, centred at reading width
  left    one photo, pushed left   / right: pushed right
  row     2-4 photos side by side, same height
  stagger two photos at different sizes, offset vertically
  strip   a horizontally scrolling film strip
  cover   the chapter's opening photo, full screen, with the chapter title on it
  sticky-l / sticky-r  one photo pinned on the left/right while the rest scroll past it
  overlap / overlap-r  a big photo with a smaller one laid over its corner
  wave    three photos side by side at different heights
  mosaic-l / mosaic-r  one large photo with two smaller ones stacked beside it
  whisper one small photo alone in a lot of space
  bleed-l / bleed-r    a photo running off the left/right edge of the screen
  sheet   a film contact sheet on a black band, frame numbers beneath
  tone    ("tone", "dark") switches the page background from this point on
"""
import html
import json
import os
from PIL import Image, ImageOps

SRC, OUT, ME = "photos", "img", "me"
SIZES = {"s": 1000, "l": 2200}

NAME = "Pratik Karmakar"
INSTAGRAM = "pkpratik"
TITLE = "Vietnam"
SITE_URL = "https://pratik2358.github.io/vietnam-photos/"

# The slideshow on the opening screen. Each photo is cropped to a tall 4:5 frame around its subject:
#   (photo, x, y, zoom): x and y are where the subject sits (0-1 across and down the photo),
#   zoom > 1 crops in tighter than the largest 4:5 frame the photo allows.
SLIDESHOW = [
    ("9174", 0.53, 0.50, 1.00),  # Hà Nội: train street; the train's headlight on the centre line
    ("9770", 0.62, 0.55, 1.10),  # Hà Nội: áo dài and umbrella, with the red pillar beside her
    ("9553", 0.52, 0.50, 1.00),  # Ninh Bình: the river winding through the karsts
    ("9389", 0.50, 0.50, 1.00),  # Ninh Bình: conical hat and life vest (already 4:5)
    ("0721", 0.32, 0.50, 1.00),  # Sa Pa: the sun rays falling on the left
    ("1027", 0.56, 0.50, 1.00),  # Sa Pa: the boys to the left, the whole flag in
    ("2302", 0.37, 0.45, 1.00),  # Hội An: the woman on the roof, with the nearer red lantern
    ("2474", 0.40, 0.50, 1.00),  # Hội An: the lit house, the moon and the lantern boat
    ("1830", 0.50, 0.62, 1.00),  # Hội An: the bridge and its reflection, less empty sky
    ("2098", 0.45, 0.50, 1.00),  # Đà Nẵng: the fishermen along the water, the man in the hat on the right
]

# The image shown when the link is shared (WhatsApp, iMessage, social media).
# FOCUS is how far down the photo (0 = top, 1 = bottom) the crop should centre on.
SHARE_PHOTO, SHARE_FOCUS = "2474", 0.55

ABOUT_TITLE = "On the other side of the lens"
ABOUT = [
    "I&rsquo;m Pratik. Most of my days go into computer science research, "
    "where nothing counts until it&rsquo;s proven.",
    "Photography is just another quirk &mdash; the one place where "
    "seeing is enough.",
]

LAYOUT = [
    {
        "id": "hanoi", "folder": "hanoi", "num": "I", "title": "Hà Nội", "sub": "from day into night",
        "rows": [
            ("cover", "9770"),
            ("whisper", "9715"),
            ("mosaic-l", "9672", "9606", "9701"),
            ("overlap", "9201", "9722"),
            ("sticky-l", "9824", "9742", "9738", "9842"),
            ("full", "9890"),
            ("tone", "dark"),
            ("full", "9174"),
            ("wave", "9121", "9026", "9016"),
            ("overlap-r", "9070", "9636"),
            ("stagger", "9085", "9096"),
            ("sticky-r", "9068", "9084", "9145", "9131"),
            ("mosaic-r", "9099", "9138", "9148"),
            ("bleed-l", "9112"),
            ("stagger", "9137", "9072"),
            ("center", "9639"),
        ],
    },
    {
        "id": "ninh-binh", "folder": "ninh_binh", "num": "II", "title": "Ninh Bình", "sub": "on the water",
        "rows": [
            ("cover", "9553"),
            ("bleed-r", "9222"),
            ("stagger", "9238", "9217"),
            ("overlap", "9271", "9389"),
            ("sticky-l", "9382", "9311", "9351", "9471"),
            ("sheet", "9385", "9395", "9411", "9414", "9424", "9485", "9488", "9491", "9500"),
            ("row", "9507", "9521"),
            ("whisper", "9544"),
        ],
    },
    {
        "id": "sapa", "folder": "sapa", "num": "III", "title": "Sa Pa", "sub": "in the clouds",
        "rows": [
            ("cover", "0721"),
            ("wave", "0709", "0716", "0717"),
            ("overlap", "0732", "0734"),
            ("sticky-l", "0786", "0779", "0794", "0821"),
            ("wave", "0771", "0813", "0828"),
            ("stagger", "0740", "0748"),
            ("tone", "dark"),
            ("bleed-l", "0835"),
            ("overlap-r", "0869", "0831"),
            ("row", "0837", "0872", "0858"),
            ("tone", "light"),
            ("full", "0952"),
            ("stagger", "0945", "0948"),
            ("whisper", "0981"),
            ("row", "0993", "0999"),
            ("row", "0941", "0942"),
            ("bleed-r", "0960"),
            ("row", "0954", "1012", "1462"),
            ("stagger", "1018", "1015_bw"),
            ("full", "1027"),
            ("sticky-r", "1447", "1095", "1503", "1507"),
            ("wave", "1547", "1549", "1579"),
            ("mosaic-l", "1601", "1599", "1603"),
            ("stagger", "1611", "1621"),
            ("wave", "1629", "1641", "1649"),
            ("center", "1645"),
            ("full", "1553"),
        ],
    },
    {
        "id": "hoi-an", "folder": "hoi_an", "num": "IV", "title": "Hội An", "sub": "by lantern light",
        "rows": [
            ("cover", "2302"),
            ("bleed-l", "1700"),
            ("stagger", "2181", "2201"),
            ("row", "2235", "2238", "2323"),
            ("overlap", "2297", "2221"),
            ("sticky-l", "2282", "2283", "2256", "2272"),
            ("whisper", "2185"),
            ("row", "2279", "2310"),
            ("bleed-r", "2313"),
            ("stagger", "2319", "2342"),
            ("mosaic-r", "2357", "2344", "2345"),
            ("row", "2369", "2379"),
            ("overlap-r", "2391", "2397"),
            ("bleed-l", "2385"),
            ("row", "2420", "2423"),
            ("stagger", "1699", "1727"),
            ("row", "2430", "2471"),
            ("full", "2474"),
            ("tone", "dark"),
            ("bleed-l", "2480"),
            ("row", "1740", "1745"),
            ("whisper", "1806"),
            ("overlap", "1764", "1776"),
            ("bleed-r", "1773"),
            ("wave", "2484", "2489", "1793"),
            ("full", "1872"),
            ("sticky-l", "1867", "1832", "1842", "1859", "1856"),
            ("wave", "1890", "1891", "1905"),
            ("center", "1895"),
            ("row", "1884", "1888"),
            ("stagger", "2517", "2520"),
            ("overlap-r", "1907", "1920"),
            ("row", "1923", "1943"),
            ("stagger", "1956", "1967"),
            ("wave", "1970", "1989", "1992"),
            ("mosaic-l", "1994", "2039", "2523"),
            ("row", "2526", "hoi_an_hair"),
            ("row", "2027", "2037"),
            ("center", "1830"),
        ],
    },
    {
        "id": "da-nang", "folder": "da_nang", "num": "V", "title": "Đà Nẵng", "sub": "the nets come in",
        "rows": [
            ("cover", "2098"),
            ("whisper", "2059"),
            ("bleed-r", "2069"),
            ("sticky-l", "2079", "2102", "1662", "2117"),
            ("right", "2146"),
            ("full", "2128"),
        ],
    },
]
# Where to centre each chapter cover when the screen crops it (CSS object-position).
COVER_FOCUS = {"9770": "64% 50%", "9553": "50% 60%", "0721": "35% 50%", "2302": "45% 45%", "2098": "55% 55%"}
NOT_PHOTOS = ("tone", "beat")  # row kinds whose entries aren't photos
COLLAPSE = True  # start each chapter as a short selection with an Explore more button


def process():
    """Resize new or changed photos; return {number: (w, h)} and {number: folder}."""
    manifest_path = f"{OUT}/sources.json"
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except FileNotFoundError:
        manifest = {}
    dims, folders = {}, {}
    for folder in sorted(os.listdir(SRC)):
        if not os.path.isdir(os.path.join(SRC, folder)):
            continue
        for f in sorted(os.listdir(os.path.join(SRC, folder))):
            if not f.lower().endswith((".jpg", ".jpeg")):
                continue
            path = os.path.join(SRC, folder, f)
            key = os.path.splitext(f)[0].replace("DSCF", "").lower()
            assert key not in folders, f"{key} is in both {folders.get(key)} and {folder}"
            folders[key] = folder
            st = os.stat(path)
            stamp = [st.st_size, int(st.st_mtime)]
            targets = {k: f"{OUT}/{k}/{key}.jpg" for k in SIZES}
            if manifest.get(key) == stamp and all(os.path.exists(t) for t in targets.values()):
                with Image.open(targets["l"]) as im:
                    dims[key] = im.size
                continue
            im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
            for k, px in SIZES.items():
                os.makedirs(f"{OUT}/{k}", exist_ok=True)
                c = im.copy()
                c.thumbnail((px, px), Image.LANCZOS)
                c.save(targets[k], quality=82, optimize=True, progressive=True)
                if k == "l":
                    dims[key] = c.size
            manifest[key] = stamp
            print("resized", path)
    # Drop resized copies of photos that were removed from photos/.
    for k in SIZES:
        for f in os.listdir(f"{OUT}/{k}"):
            if os.path.splitext(f)[0] not in dims:
                os.remove(f"{OUT}/{k}/{f}")
                print("removed", f"{OUT}/{k}/{f}")
    manifest = {k: v for k, v in manifest.items() if k in dims}
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=0, sort_keys=True)
    return dims, folders


def add_unplaced(chapter, placed, folders):
    """Append photos from the chapter's folder that LAYOUT doesn't mention."""
    extra = sorted(k for k, f in folders.items() if f == chapter["folder"] and k not in placed)
    if extra:
        print(f"note: added to the end of {chapter['folder']}: {extra}")
    for i in range(0, len(extra), 2):
        pair = extra[i:i + 2]
        chapter["rows"].append(("row", *pair) if len(pair) == 2 else ("center", pair[0]))


def source(key, folders):
    """Path of the original photo for a key like "9553"."""
    d = os.path.join(SRC, folders[key])
    return next(os.path.join(d, f) for f in os.listdir(d)
                if os.path.splitext(f)[0].replace("DSCF", "").lower() == key)


def slideshow(folders):
    """Crop the SLIDESHOW photos to 4:5 into img/show/; returns the slideshow markup."""
    os.makedirs(f"{OUT}/show", exist_ok=True)
    keep = set()
    for key, fx, fy, zoom in SLIDESHOW:
        out = f"{OUT}/show/{key}.jpg"
        keep.add(f"{key}.jpg")
        im = ImageOps.exif_transpose(Image.open(source(key, folders))).convert("RGB")
        w, h = im.size
        cw, ch = (h * 4 / 5, h) if w / h > 4 / 5 else (w, w * 5 / 4)
        cw, ch = round(cw / zoom), round(ch / zoom)
        left = min(max(0, round(w * fx - cw / 2)), w - cw)
        top = min(max(0, round(h * fy - ch / 2)), h - ch)
        im.crop((left, top, left + cw, top + ch)).resize((1000, 1250), Image.LANCZOS).save(
            out, quality=82, optimize=True, progressive=True)
    for f in os.listdir(f"{OUT}/show"):
        if f not in keep:
            os.remove(f"{OUT}/show/{f}")
    # Only the first slide loads with the page; script.js loads each next one just before it shows.
    imgs = "".join(
        (f'<img src="{OUT}/show/{k}.jpg" class="on"' if i == 0 else f'<img data-src="{OUT}/show/{k}.jpg"')
        + ' alt="" width="1000" height="1250">'
        for i, (k, *_) in enumerate(SLIDESHOW))
    return f'<div class="show" aria-hidden="true">{imgs}</div>'


def share_image(folders):
    """Crop SHARE_PHOTO to 1200x630, the shape link previews use, as img/share.jpg."""
    im = ImageOps.exif_transpose(Image.open(source(SHARE_PHOTO, folders))).convert("RGB")
    w, h = im.size
    ch = min(h, round(w * 630 / 1200))
    top = min(max(0, round(h * SHARE_FOCUS - ch / 2)), h - ch)
    im.crop((0, top, w, top + ch)).resize((1200, 630), Image.LANCZOS).save(
        f"{OUT}/share.jpg", quality=85, optimize=True, progressive=True)


def figure(key, dims, sizes, cls="", eager=False, base=OUT, alt=""):
    w, h = dims[key]
    load = "eager" if eager else "lazy"
    style = f' style="--ar:{w / h:.4f}"'
    return (
        f'<figure class="ph {cls}"{style}>'
        f'<img src="{base}/s/{key}.jpg" srcset="{base}/s/{key}.jpg 1000w, {base}/l/{key}.jpg 2200w" '
        f'sizes="{sizes}" width="{w}" height="{h}" loading="{load}" decoding="async" '
        f'alt="{html.escape(alt)}" data-full="{base}/l/{key}.jpg"></figure>'
    )


def about():
    """The closing About section: the photographer, for once in front of the lens."""
    base = f"{OUT}/me"
    dims = {}
    for f in sorted(os.listdir(ME)):
        if not f.lower().endswith((".jpg", ".jpeg")):
            continue
        key = os.path.splitext(f)[0].lower()
        targets = {k: f"{base}/{k}/{key}.jpg" for k in SIZES}
        if all(os.path.exists(t) and os.path.getmtime(t) >= os.path.getmtime(os.path.join(ME, f))
               for t in targets.values()):
            with Image.open(targets["l"]) as im:
                dims[key] = im.size
            continue
        im = ImageOps.exif_transpose(Image.open(os.path.join(ME, f))).convert("RGB")
        for k, px in SIZES.items():
            os.makedirs(f"{base}/{k}", exist_ok=True)
            c = im.copy()
            c.thumbnail((px, px), Image.LANCZOS)
            c.save(targets[k], quality=82, optimize=True, progressive=True)
            if k == "l":
                dims[key] = c.size
        print("resized", os.path.join(ME, f))
    # The tallest photo anchors the mosaic; the rest stack beside it.
    keys = sorted(dims, key=lambda k: dims[k][0] / dims[k][1])
    tall, rest = keys[0], keys[1:]
    alt = f"{NAME} with a camera"
    figs = figure(tall, dims, "(max-width: 700px) 100vw, 26vw", "tall", base=base, alt=alt)
    figs += "".join(figure(k, dims, "(max-width: 700px) 100vw, 34vw", "side", base=base, alt=alt)
                    for k in rest)
    text = "".join(f"<p>{p}</p>" for p in ABOUT)
    return (f'<section id="about" class="about"><div class="about-text">'
            f'<p class="kicker">About</p><h2>{ABOUT_TITLE}</h2>{text}</div>'
            f'<div class="about-photos">{figs}</div></section>')


def render_row(row, dims, first, head=""):
    kind, keys = row[0], row[1:]
    half, third = "(max-width: 700px) 100vw, 50vw", "(max-width: 700px) 100vw, 34vw"
    if kind == "cover":
        focus = COVER_FOCUS.get(keys[0], "50% 50%")
        return (f'<div class="r cover" style="--focus:{focus}">{figure(keys[0], dims, "100vw", eager=True)}'
                f'{head}</div>')
    if kind == "beat":
        return f'<div class="r beat"><p>{html.escape(keys[0])}</p></div>'
    if kind in ("bleed-l", "bleed-r"):
        return f'<div class="r bleed {kind}">{figure(keys[0], dims, "(max-width: 700px) 100vw, 75vw")}</div>'
    if kind == "whisper":
        return f'<div class="r whisper">{figure(keys[0], dims, "(max-width: 700px) 60vw, 30vw")}</div>'
    if kind in ("overlap", "overlap-r"):
        big, small = keys
        return (f'<div class="r overlap {kind}">{figure(big, dims, "(max-width: 700px) 100vw, 64vw", "big")}'
                f'{figure(small, dims, "(max-width: 700px) 55vw, 30vw", "small")}</div>')
    if kind in ("sticky-l", "sticky-r"):
        pin, rest = keys[0], keys[1:]
        return (f'<div class="r sticky {kind}"><div class="pin">{figure(pin, dims, half)}</div>'
                f'<div class="col">{"".join(figure(k, dims, half) for k in rest)}</div></div>')
    if kind == "wave":
        return '<div class="r wave">' + "".join(figure(k, dims, third) for k in keys) + "</div>"
    if kind in ("mosaic-l", "mosaic-r"):
        big, *small = keys
        return (f'<div class="r mosaic {kind}"><div class="m">{figure(big, dims, "(max-width: 700px) 100vw, 60vw", "big")}'
                + "".join(figure(k, dims, third) for k in small) + '</div></div>')
    if kind == "sheet":
        frames = "".join(f'<div class="frame">{figure(k, dims, third)}<span>{k}</span></div>' for k in keys)
        return f'<div class="r sheet"><div class="film">{frames}</div></div>'
    if kind == "full":
        return f'<div class="r full">{figure(keys[0], dims, "100vw", eager=first)}</div>'
    if kind in ("center", "left", "right"):
        return f'<div class="r solo {kind}">{figure(keys[0], dims, "(max-width: 700px) 100vw, 70vw")}</div>'
    if kind == "row":
        sz = f"(max-width: 700px) 100vw, {100 // len(keys) + 10}vw"
        return '<div class="r row">' + "".join(figure(k, dims, sz) for k in keys) + "</div>"
    if kind == "stagger":
        a, b = keys
        return (f'<div class="r stagger">{figure(a, dims, "(max-width: 700px) 100vw, 40vw", "a")}'
                f'{figure(b, dims, "(max-width: 700px) 100vw, 60vw", "b")}</div>')
    if kind == "strip":
        figs = "".join(figure(k, dims, "(max-width: 700px) 80vw, 45vw") for k in keys)
        return (f'<div class="r strip"><div class="track">{figs}</div>'
                f'<p class="hint">scroll &rarr;</p></div>')
    raise ValueError(kind)


TEASER = 5        # photos to show at the start of each part while a chapter is collapsed
MIN_HIDDEN = 4    # don't collapse a chapter to hide fewer photos than this


def teaser(parts):
    """Pick which rows to hide while the chapter is collapsed; returns their ids.

    Each part keeps its opening rows (about TEASER photos) and its closing row, so a
    collapsed chapter still moves from day into night and still ends on its last photo.
    """
    if not COLLAPSE:
        return set()
    # Fewer per part when a chapter has several (Sa Pa: day, night, the next day).
    per_part = {1: TEASER + 3, 2: TEASER}.get(len(parts), TEASER - 2)
    extra = set()
    for _, rows in parts:
        shown = 0
        for i, r in enumerate(rows):
            if shown >= per_part and i != len(rows) - 1:
                extra.add(id(r))
            else:
                shown += len(r) - 1
    hidden = sum(len(r) - 1 for _, rows in parts for r in rows if id(r) in extra)
    return extra if hidden >= MIN_HIDDEN else set()


def more_button(chapter, hidden):
    """The Explore more / Show less button, with a small fan of hidden photos."""
    picks = [hidden[round(i * (len(hidden) - 1) / 2)] for i in range(3)]
    thumbs = "".join(f'<img src="{OUT}/s/{k}.jpg" alt="" loading="lazy" decoding="async">' for k in picks)
    title = html.escape(chapter["title"])
    return (f'<div class="more"><button class="more-btn" type="button" aria-expanded="false">'
            f'<span class="more-thumbs" aria-hidden="true">{thumbs}</span>'
            f'<span class="more-open">Explore more of {title}</span>'
            f'<span class="more-close">Show less</span>'
            f'<span class="more-arrow" aria-hidden="true">&darr;</span></button></div>')


def build():
    dims, folders = process()
    share_image(folders)

    def placed():
        return [k for ch in LAYOUT for r in ch["rows"] if r[0] not in NOT_PHOTOS for k in r[1:]]

    used = placed()
    unknown = [k for k in used if k not in dims]
    dupes = {k for k in used if used.count(k) > 1}
    assert not unknown, f"photos in LAYOUT but not in photos/: {unknown}"
    assert not dupes, f"photos used twice: {dupes}"
    for ch in LAYOUT:
        for r in ch["rows"]:
            for k in r[1:] if r[0] not in NOT_PHOTOS else ():
                if folders[k] != ch["folder"]:
                    print(f"warning: {k} is in photos/{folders[k]} but LAYOUT puts it in {ch['id']}")
    for ch in LAYOUT:
        add_unplaced(ch, set(used), folders)
    used = placed()
    orphans = sorted(set(dims) - set(used))
    if orphans:
        print("note: in folders with no chapter, not shown:", orphans)

    nav = "".join(
        f'<li><a href="#{c["id"]}"><span>{c["num"]}</span>{html.escape(c["title"])} '
        f'<em>{c["sub"]}</em></a></li>' for c in LAYOUT)
    body = []
    for n, c in enumerate(LAYOUT):
        head = (f'<header class="ch-head"><span class="num">{c["num"]}</span>'
                f'<h2>{html.escape(c["title"])}</h2><p>{c["sub"]}</p></header>')
        # A ("tone", "dark"|"light") row starts a new part; the page background follows it.
        parts = [["light", []]]
        for r in c["rows"]:
            if r[0] == "tone":
                parts.append([r[1], []])
            else:
                parts[-1][1].append(r)
        extra = teaser(parts)
        hidden = [k for _, rows in parts for r in rows if id(r) in extra for k in r[1:]]
        inner = ""
        for p_i, (tone, rows) in enumerate(parts):
            has_cover = c["rows"][0][0] == "cover"
            h = head if p_i == 0 and not has_cover else ""
            for r in rows:
                row_html = render_row(r, dims, n == 0 and r is c["rows"][0],
                                      head.replace('class="ch-head"', 'class="ch-head on-photo"') if r[0] == "cover" else "")
                if id(r) in extra:
                    row_html = row_html.replace('<div class="r ', '<div class="r extra ', 1)
                h += row_html
            inner += f'<div class="part" data-tone="{tone}">{h}</div>'
        if hidden:
            inner += more_button(c, hidden)
        body.append(f'<section id="{c["id"]}" class="chapter">{inner}</section>')

    with open("template.html") as f:
        page = f.read()
    page = (page.replace("{{TITLE}}", TITLE).replace("{{NAME}}", NAME)
            .replace("{{SITE_URL}}", SITE_URL)
            .replace("{{SLIDESHOW}}", slideshow(folders))
            .replace("{{INSTAGRAM}}", INSTAGRAM)
            .replace("{{NAV}}", nav).replace("{{CHAPTERS}}", "".join(body)).replace("{{ABOUT}}", about()))
    with open("index.html", "w") as f:
        f.write(page)
    print(f"index.html written: {len(used)} photos, {len(LAYOUT)} chapters")


if __name__ == "__main__":
    build()
