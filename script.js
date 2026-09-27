(() => {
  const figs = [...document.querySelectorAll('.ph')];

  // Fade photos in as they arrive.
  const reveal = new IntersectionObserver(entries => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add('in'); reveal.unobserve(e.target); }
  }, { rootMargin: '0px 0px -8% 0px' });
  figs.forEach(f => reveal.observe(f));

  // The page background follows the part of the page in the middle of the screen.
  const tone = new IntersectionObserver(entries => {
    for (const e of entries) if (e.isIntersecting) document.body.dataset.tone = e.target.dataset.tone;
  }, { rootMargin: '-50% 0px -50% 0px' });
  document.querySelectorAll('.intro, .part, .about, .end').forEach(s => {
    if (!s.dataset.tone) s.dataset.tone = 'light';
    tone.observe(s);
  });

  // Lightbox: only the trip's photos, not the About portraits.
  const shots = [...document.querySelectorAll('.chapter .ph')];
  const lb = document.querySelector('.lb');
  const img = lb.querySelector('img');
  const cap = lb.querySelector('.lb-c');
  let i = 0;
  const show = n => {
    i = (n + shots.length) % shots.length;
    img.src = shots[i].querySelector('img').dataset.full;
    cap.textContent = `${i + 1} / ${shots.length}`;
    // social.js listens for this to load the photo's likes and comments.
    const photo = img.src.split('/').pop().replace(/\.jpg$/, '');
    lb.dispatchEvent(new CustomEvent('photo', { detail: photo }));
  };
  const open = n => { show(n); lb.hidden = false; document.body.style.overflow = 'hidden'; };
  const close = () => {
    if (isFull()) exitFull();
    lb.hidden = true; img.removeAttribute('src'); document.body.style.overflow = '';
    lb.dispatchEvent(new Event('closed'));
  };

  // Full screen, from the button on each photo or the one in the viewer. Browsers that can't
  // put a page element in full screen (iPhone Safari) get no buttons; the viewer still works.
  const canFull = document.fullscreenEnabled || document.webkitFullscreenEnabled;
  const isFull = () => !!(document.fullscreenElement || document.webkitFullscreenElement);
  const exitFull = () => (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  const enterFull = () => {
    const req = (lb.requestFullscreen || lb.webkitRequestFullscreen).call(lb);
    if (req && req.catch) req.catch(() => {});
  };
  // Full screen entered from a photo on the page returns to the page when it ends;
  // entered from the viewer, it returns to the viewer.
  let backToPage = false;
  const onFullChange = () => {
    lb.classList.toggle('full', isFull());
    if (!isFull() && !lb.hidden && backToPage) close();
  };
  const lbFs = lb.querySelector('.lb-fs');
  if (!canFull) lbFs.hidden = true;
  lbFs.onclick = e => {
    e.stopPropagation();
    if (isFull()) exitFull();
    else { backToPage = false; enterFull(); }
  };
  document.addEventListener('fullscreenchange', onFullChange);
  document.addEventListener('webkitfullscreenchange', onFullChange);

  shots.forEach((f, n) => {
    f.addEventListener('click', () => open(n));
    if (!canFull) return;
    const b = document.createElement('button');
    b.className = 'fs';
    b.type = 'button';
    b.setAttribute('aria-label', 'View full screen');
    b.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" '
      + 'stroke-width="1.6"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';
    b.addEventListener('click', e => { e.stopPropagation(); open(n); backToPage = true; enterFull(); });
    f.appendChild(b);
  });
  lb.querySelector('.lb-x').onclick = close;
  lb.querySelector('.lb-p').onclick = e => { e.stopPropagation(); show(i - 1); };
  lb.querySelector('.lb-n').onclick = e => { e.stopPropagation(); show(i + 1); };
  lb.addEventListener('click', e => { if (e.target === lb) close(); });
  addEventListener('keydown', e => {
    if (lb.hidden || e.target.closest('input, textarea')) return;  // typing a comment
    if (e.key === 'Escape') {
      if (lb.classList.contains('talking')) lb.dispatchEvent(new Event('closepanel'));
      else close();
    }
    if (e.key === 'ArrowLeft') show(i - 1);
    if (e.key === 'ArrowRight') show(i + 1);
  });

  let x0 = null;
  lb.addEventListener('touchstart', e => {
    x0 = e.target.closest('.lb-panel, .lb-foot') ? null : e.touches[0].clientX;
  }, { passive: true });
  lb.addEventListener('touchend', e => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1));
    x0 = null;
  });
})();
