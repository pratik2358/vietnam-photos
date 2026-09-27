// Likes and comments in the photo viewer, stored in Firebase (Firestore).
// Firebase only loads the first time someone opens a photo. If it can't load
// (offline, blocked), the like and comment controls simply stay hidden.
//
// Data:
//   likes/{photo}   { n }                                     one counter per photo
//   comments/{id}   { photo, name, text, created, approved }  hidden until approved
// Approve a comment in the Firebase console: Firestore → comments → set approved to true.

const FIREBASE = 'https://www.gstatic.com/firebasejs/12.19.0';
const config = {
  apiKey: 'AIzaSyC1pL9jGJ-YwQxoWH42bRiV98XIpg5eRN0',
  authDomain: 'vietnam-photos-pratik.firebaseapp.com',
  projectId: 'vietnam-photos-pratik',
  storageBucket: 'vietnam-photos-pratik.firebasestorage.app',
  messagingSenderId: '259999771597',
  appId: '1:259999771597:web:e4a3850d472b6fbc9f3284',
};

const lb = document.querySelector('.lb');
const social = lb.querySelector('.lb-social');
const likeBtn = lb.querySelector('.lb-like');
const likeN = likeBtn.querySelector('span');
const talkBtn = lb.querySelector('.lb-talk');
const talkN = talkBtn.querySelector('span');
const panel = lb.querySelector('.lb-panel');
const list = panel.querySelector('.lb-comments');
const empty = panel.querySelector('.lb-empty');
const form = panel.querySelector('form');
const note = panel.querySelector('.lb-note');

const store = {
  get: k => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} },
};

let fb = null;       // loaded Firebase functions and database
let current = null;  // the photo on screen
const cache = new Map();  // photo -> { likes, comments[] }

function load() {
  fb ??= (async () => {
    const [{ initializeApp }, fs] = await Promise.all([
      import(`${FIREBASE}/firebase-app.js`),
      import(`${FIREBASE}/firebase-firestore-lite.js`),
    ]);
    return { ...fs, db: fs.getFirestore(initializeApp(config)) };
  })();
  return fb;
}

async function fetchPhoto(photo) {
  if (cache.has(photo)) return cache.get(photo);
  const f = await load();
  const [likeDoc, snap] = await Promise.all([
    f.getDoc(f.doc(f.db, 'likes', photo)),
    f.getDocs(f.query(f.collection(f.db, 'comments'),
      f.where('photo', '==', photo), f.where('approved', '==', true))),
  ]);
  const comments = snap.docs.map(d => d.data())
    .sort((a, b) => (a.created?.toMillis?.() ?? 0) - (b.created?.toMillis?.() ?? 0));
  const data = { likes: likeDoc.exists() ? likeDoc.data().n : 0, comments };
  cache.set(photo, data);
  return data;
}

function render(photo) {
  const d = cache.get(photo);
  if (!d || photo !== current) return;
  const liked = store.get(`liked:${photo}`) === '1';
  likeBtn.classList.toggle('on', liked);
  likeBtn.setAttribute('aria-pressed', liked);
  likeBtn.setAttribute('aria-label', liked ? 'Unlike' : 'Like');
  likeN.textContent = d.likes || '';
  talkN.textContent = d.comments.length || '';
  list.replaceChildren(...d.comments.map(c => {
    const li = document.createElement('li');
    const who = document.createElement('p');
    who.className = 'who';
    who.textContent = c.name;
    const when = c.created?.toDate?.();
    if (when) {
      const t = document.createElement('time');
      t.textContent = when.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
      who.append(' ', t);
    }
    const text = document.createElement('p');
    text.textContent = c.text;
    li.append(who, text);
    return li;
  }));
  empty.hidden = d.comments.length > 0;
}

lb.addEventListener('photo', async e => {
  current = e.detail;
  note.textContent = '';
  if (!cache.has(current)) { likeN.textContent = ''; talkN.textContent = ''; list.replaceChildren(); empty.hidden = true; }
  try {
    await fetchPhoto(current);
    social.hidden = false;
    render(e.detail);
  } catch (err) {
    console.warn('Likes and comments unavailable:', err);
  }
});

likeBtn.addEventListener('click', async e => {
  e.stopPropagation();
  const photo = current, d = cache.get(photo);
  if (!d) return;
  const liked = store.get(`liked:${photo}`) === '1';
  const step = liked ? -1 : 1;
  // Show the change straight away; undo it if the write fails.
  d.likes = Math.max(0, d.likes + step);
  store.set(`liked:${photo}`, liked ? null : '1');
  render(photo);
  try {
    const f = await load();
    await f.setDoc(f.doc(f.db, 'likes', photo), { n: f.increment(step) }, { merge: true });
  } catch (err) {
    d.likes = Math.max(0, d.likes - step);
    store.set(`liked:${photo}`, liked ? '1' : null);
    render(photo);
    console.warn('Like failed:', err);
  }
});

const openPanel = () => { panel.hidden = false; lb.classList.add('talking'); };
const closePanel = () => { panel.hidden = true; lb.classList.remove('talking'); };
talkBtn.addEventListener('click', e => { e.stopPropagation(); panel.hidden ? openPanel() : closePanel(); });
panel.querySelector('.lb-panel-x').addEventListener('click', closePanel);
lb.addEventListener('closepanel', closePanel);
lb.addEventListener('closed', closePanel);
panel.addEventListener('keydown', e => { if (e.key === 'Escape') closePanel(); });

form.name.value = store.get('comment-name') || '';
let sending = false;
form.addEventListener('submit', async e => {
  e.preventDefault();
  if (sending) return;
  const name = form.name.value.trim(), text = form.text.value.trim();
  if (!name || !text) return;
  const thanks = 'Thank you — your comment will appear once it’s approved.';
  // The hidden "website" field is invisible to people; bots that fill it get a fake success.
  if (form.website.value) { form.text.value = ''; note.textContent = thanks; return; }
  sending = true;
  form.querySelector('button').disabled = true;
  note.textContent = 'Sending…';
  try {
    const f = await load();
    await f.addDoc(f.collection(f.db, 'comments'), {
      photo: current, name: name.slice(0, 60), text: text.slice(0, 1000),
      created: f.serverTimestamp(), approved: false,
    });
    store.set('comment-name', name);
    form.text.value = '';
    note.textContent = thanks;
  } catch (err) {
    note.textContent = 'Sorry, that didn’t go through. Please try again.';
    console.warn('Comment failed:', err);
  } finally {
    sending = false;
    form.querySelector('button').disabled = false;
  }
});
