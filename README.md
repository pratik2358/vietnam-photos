# Vietnam

Photographs by Pratik Karmakar: Hà Nội, Ninh Bình, Sa Pa, Hội An and Đà Nẵng.

The page is plain HTML, CSS and JS, served by GitHub Pages.

Originals live in one folder per chapter: `photos/hanoi`, `photos/ninh_binh`, `photos/sapa`, `photos/hoi_an`, `photos/da_nang`.
To add a photo, drop it into its chapter's folder; it is placed at the end of that chapter
until you give it a spot in `LAYOUT` in `build.py`. Then run:

    python3 build.py

This resizes new photos into `img/` and rewrites `index.html` from `template.html`.
The original photos stay local and are not committed.

## Likes and comments

Likes and comments live in Firebase (project `vietnam-photos-pratik`, Firestore) and are handled by `social.js`.
Visitors don't sign in. Likes count once per browser. Comments stay hidden until approved.

To moderate, open the Firebase console → Firestore → Data → `comments`:
- **Approve:** open the comment and change `approved` from `false` to `true`.
- **Remove:** delete the document.

The security rules (Firestore → Rules) only let visitors add or remove one like at a time,
submit comments as unapproved, and read approved comments.
