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
  tone    ("tone", "dark") switches the page background from this point on
"""
import html
import json
import os
from PIL import Image, ImageOps

SRC, OUT = "photos", "img"
SIZES = {"s": 1000, "l": 2200}

NAME = "Pratik Karmakar"
INSTAGRAM = "pkpratik"
TITLE = "Vietnam"

LAYOUT = [
    {
        "id": "hanoi", "folder": "hanoi", "num": "I", "title": "Hà Nội", "sub": "from day into night",
        "rows": [
            ("center", "9672"),
            ("stagger", "9606", "9201"),
            ("row", "9715", "9648"),
            ("row", "9701", "9722"),
            ("center", "9770"),
            ("row", "9790", "9803", "9824"),
            ("row", "9822", "9742"),
            ("row", "9738", "9842"),
            ("full", "9890"),
            ("tone", "dark"),
            ("full", "9174"),
            ("row", "9070", "9121"),
            ("row", "9026", "9636"),
            ("row", "9010", "9016", "9044"),
            ("stagger", "9052", "9072"),
            ("center", "9145"),
            ("row", "9085", "9096"),
            ("row", "9068", "9084"),
            ("left", "9131"),
            ("row", "9099", "9138", "9148"),
            ("row", "9112", "9137"),
            ("left", "9639"),
            ("center", "9160"),
        ],
    },
    {
        "id": "ninh-binh", "folder": "ninh_binh", "num": "II", "title": "Ninh Bình", "sub": "on the water",
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
        "id": "sapa", "folder": "sapa", "num": "III", "title": "Sa Pa", "sub": "in the clouds",
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
    dims, folders = process()

    def placed():
        return [k for ch in LAYOUT for r in ch["rows"] if r[0] != "tone" for k in r[1:]]

    used = placed()
    unknown = [k for k in used if k not in dims]
    dupes = {k for k in used if used.count(k) > 1}
    assert not unknown, f"photos in LAYOUT but not in photos/: {unknown}"
    assert not dupes, f"photos used twice: {dupes}"
    for ch in LAYOUT:
        for r in ch["rows"]:
            for k in r[1:] if r[0] != "tone" else ():
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
        # A ("tone", "dark"|"light") row starts a new part; the page background follows it.
        parts = [["light", f'<header class="ch-head"><span class="num">{c["num"]}</span>'
                           f'<h2>{html.escape(c["title"])}</h2><p>{c["sub"]}</p></header>']]
        for i, r in enumerate(c["rows"]):
            if r[0] == "tone":
                parts.append([r[1], ""])
            else:
                parts[-1][1] += render_row(r, dims, n == 0 and i == 0)
        inner = "".join(f'<div class="part" data-tone="{t}">{h}</div>' for t, h in parts)
        body.append(f'<section id="{c["id"]}" class="chapter">{inner}</section>')

    with open("template.html") as f:
        page = f.read()
    page = (page.replace("{{TITLE}}", TITLE).replace("{{NAME}}", NAME)
            .replace("{{INSTAGRAM}}", INSTAGRAM)
            .replace("{{NAV}}", nav).replace("{{CHAPTERS}}", "".join(body))
            .replace("{{COUNT}}", str(len(used))))
    with open("index.html", "w") as f:
        f.write(page)
    print(f"index.html written: {len(used)} photos, {len(LAYOUT)} chapters")


if __name__ == "__main__":
    build()
