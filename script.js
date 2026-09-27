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
  };
  const open = n => { show(n); lb.hidden = false; document.body.style.overflow = 'hidden'; };
  const close = () => {
    if (isFull()) exitFull();
    lb.hidden = true; img.removeAttribute('src'); document.body.style.overflow = '';
  };

  // Full screen, from the button on each photo. Browsers that can't put a page element
  // in full screen (iPhone Safari) get no button; clicking the photo still opens the viewer.
  const canFull = document.fullscreenEnabled || document.webkitFullscreenEnabled;
  const isFull = () => !!(document.fullscreenElement || document.webkitFullscreenElement);
  const exitFull = () => (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  const enterFull = () => {
    const req = (lb.requestFullscreen || lb.webkitRequestFullscreen).call(lb);
    if (req && req.catch) req.catch(() => {});
  };
  const onFullChange = () => {
    lb.classList.toggle('full', isFull());
    if (!isFull() && !lb.hidden) close();  // leaving full screen goes straight back to the page
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
    b.addEventListener('click', e => { e.stopPropagation(); open(n); enterFull(); });
    f.appendChild(b);
  });
  lb.querySelector('.lb-x').onclick = close;
  lb.querySelector('.lb-p').onclick = e => { e.stopPropagation(); show(i - 1); };
  lb.querySelector('.lb-n').onclick = e => { e.stopPropagation(); show(i + 1); };
  lb.addEventListener('click', e => { if (e.target === lb) close(); });
  addEventListener('keydown', e => {
    if (lb.hidden) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') show(i - 1);
    if (e.key === 'ArrowRight') show(i + 1);
  });

  let x0 = null;
  lb.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', e => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1));
    x0 = null;
  });
})();
