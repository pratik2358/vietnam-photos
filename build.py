"""Build the site: resize photos/ into img/ and write index.html from LAYOUT.

Usage: python3 build.py
Photos are referenced by file number (e.g. "9553" -> DSCF9553.jpg).
Row types:
  full    one photo, edge to edge
  center  one photo, centred at reading width
  left    one photo, pushed left   / right: pushed right
  row     2-4 photos side by side, same height
  stagger two photos at different sizes, offset vertically
  strip   a horizontally scrolling film strip
"""
import html
import os
from PIL import Image, ImageOps

SRC, OUT = "photos", "img"
SIZES = {"s": 1000, "l": 2200}

NAME = "Pratik Karmakar"
TITLE = "Vietnam"

LAYOUT = [
    {
        "id": "hanoi-night", "num": "I", "title": "Hà Nội", "sub": "after dark", "tone": "dark",
        "rows": [
            ("full", "9174"),
            ("row", "9070", "9121"),
            ("right", "9026"),
            ("row", "9010", "9016", "9044"),
            ("stagger", "9052", "9072"),
            ("center", "9145"),
            ("row", "9085", "9096"),
            ("row", "9068", "9084"),
            ("left", "9131"),
            ("row", "9099", "9138", "9148"),
            ("row", "9112", "9137"),
            ("center", "9160"),
            ("right", "9201"),
        ],
    },
    {
        "id": "ninh-binh", "num": "II", "title": "Ninh Bình", "sub": "on the water", "tone": "light",
        "rows": [
            ("full", "9553"),
            ("stagger", "9238", "9222"),
            ("left", "9217"),
            ("row", "9271", "9311"),
            ("right", "9351"),
            ("row", "9382", "9389"),
            ("center", "9471"),
            ("strip", "9385", "9395", "9411", "9414", "9424", "9485", "9486",
             "9488", "9491", "9492", "9500"),
            ("row", "9477", "9507"),
            ("stagger", "9521", "9544"),
        ],
    },
    {
        "id": "hanoi-day", "num": "III", "title": "Hà Nội", "sub": "by day", "tone": "light",
        "rows": [
            ("center", "9672"),
            ("row", "9606", "9636"),
            ("stagger", "9715", "9648"),
            ("row", "9701", "9722"),
            ("left", "9639"),
            ("center", "9770"),
            ("row", "9790", "9803", "9824"),
            ("row", "9822", "9742"),
            ("row", "9738", "9842"),
            ("full", "9890"),
        ],
    },
    {
        "id": "sapa", "num": "IV", "title": "Sa Pa", "sub": "in the clouds", "tone": "light",
        "rows": [
            ("full", "0721"),
            ("row", "0709", "0716", "0717"),
            ("right", "0703"),
            ("row", "0732", "0734"),
            ("left", "0740"),
            ("stagger", "0748", "0771"),
            ("row", "0779", "0786"),
            ("row", "0794", "0797"),
            ("stagger", "0813", "0821"),
            ("row", "0828", "0831"),
            ("center", "0842"),
            ("row", "0835", "0837", "0872"),
            ("row", "0858", "0869"),
            ("row", "0941", "0942"),
            ("center", "0952"),
            ("row", "0945", "0948"),
            ("right", "0954"),
            ("row", "0960", "0981"),
            ("row", "0993", "0999"),
            ("left", "1008"),
            ("row", "1012", "1462"),
            ("row", "1015_bw", "1018"),
            ("full", "1027"),
            ("row", "1095", "1447"),
            ("row", "1503", "1507"),
            ("row", "1547", "1549"),
            ("center", "1562"),
            ("row", "1569", "1579", "1599"),
            ("row", "1601", "1603"),
            ("stagger", "1611", "1621"),
            ("row", "1629", "1641", "1649"),
            ("center", "1645"),
            ("full", "1553"),
        ],
    },
]


def process():
    """Resize every photo once; return {number: (w, h)}."""
    dims = {}
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith((".jpg", ".jpeg")):
            continue
        key = os.path.splitext(f)[0].replace("DSCF", "").lower()
        targets = {k: f"{OUT}/{k}/{key}.jpg" for k in SIZES}
        if all(os.path.exists(t) for t in targets.values()):
            with Image.open(targets["l"]) as im:
                dims[key] = im.size
            continue
        im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, f))).convert("RGB")
        for k, px in SIZES.items():
            os.makedirs(f"{OUT}/{k}", exist_ok=True)
            c = im.copy()
            c.thumbnail((px, px), Image.LANCZOS)
            c.save(targets[k], quality=82, optimize=True, progressive=True)
            if k == "l":
                dims[key] = c.size
        print("resized", f)
    return dims


def figure(key, dims, sizes, cls="", eager=False):
    w, h = dims[key]
    load = "eager" if eager else "lazy"
    style = f' style="--ar:{w / h:.4f}"'
    return (
        f'<figure class="ph {cls}"{style}>'
        f'<img src="{OUT}/s/{key}.jpg" srcset="{OUT}/s/{key}.jpg 1000w, {OUT}/l/{key}.jpg 2200w" '
        f'sizes="{sizes}" width="{w}" height="{h}" loading="{load}" decoding="async" alt="" '
        f'data-full="{OUT}/l/{key}.jpg"></figure>'
    )


def render_row(row, dims, first):
    kind, keys = row[0], row[1:]
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


def build():
    dims = process()
    used = [k for ch in LAYOUT for r in ch["rows"] for k in r[1:]]
    missing, dupes = set(dims) - set(used), {k for k in used if used.count(k) > 1}
    unknown = set(used) - set(dims)
    assert not unknown, f"unknown photos in LAYOUT: {unknown}"
    assert not dupes, f"photos used twice: {dupes}"
    if missing:
        print("note: not placed in LAYOUT:", sorted(missing))

    nav = "".join(
        f'<li><a href="#{c["id"]}"><span>{c["num"]}</span>{html.escape(c["title"])} '
        f'<em>{c["sub"]}</em></a></li>' for c in LAYOUT)
    body, first = [], True
    for c in LAYOUT:
        rows = "".join(render_row(r, dims, first and i == 0) for i, r in enumerate(c["rows"]))
        first = False
        body.append(
            f'<section id="{c["id"]}" class="chapter" data-tone="{c["tone"]}">'
            f'<header class="ch-head"><span class="num">{c["num"]}</span>'
            f'<h2>{html.escape(c["title"])}</h2><p>{c["sub"]}</p></header>{rows}</section>')

    with open("template.html") as f:
        page = f.read()
    page = (page.replace("{{TITLE}}", TITLE).replace("{{NAME}}", NAME)
            .replace("{{NAV}}", nav).replace("{{CHAPTERS}}", "".join(body))
            .replace("{{COUNT}}", str(len(used))))
    with open("index.html", "w") as f:
        f.write(page)
    print(f"index.html written: {len(used)} photos, {len(LAYOUT)} chapters")


if __name__ == "__main__":
    build()
