# Vietnam

Photographs by Pratik Karmakar: Hà Nội, Ninh Bình, Sa Pa, Hội An and Đà Nẵng.

The page is plain HTML, CSS and JS, served by GitHub Pages.

Originals live in one folder per chapter: `photos/hanoi`, `photos/ninh_binh`, `photos/sapa`, `photos/hoi_an`, `photos/da_nang`.
To add a photo, drop it into its chapter's folder; it is placed at the end of that chapter
until you give it a spot in `LAYOUT` in `build.py`. Then run:

    python3 build.py

This resizes new photos into `img/` and rewrites `index.html` from `template.html`.
The original photos stay local and are not committed.
