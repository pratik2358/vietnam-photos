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

  // Lightbox.
  const lb = document.querySelector('.lb');
  const img = lb.querySelector('img');
  const cap = lb.querySelector('.lb-c');
  const place = f => f.closest('.chapter')?.querySelector('h2')?.textContent || 'About';
  let i = 0;
  const show = n => {
    i = (n + figs.length) % figs.length;
    img.src = figs[i].querySelector('img').dataset.full;
    cap.textContent = `${place(figs[i])} \u00b7 ${i + 1} / ${figs.length}`;
    // Warm the cache for the next photo so stepping through feels instant.
    new Image().src = figs[(i + 1) % figs.length].querySelector('img').dataset.full;
  };
  const open = n => { show(n); lb.hidden = false; document.body.style.overflow = 'hidden'; };
  const close = () => {
    if (isFull()) exitFull();
    lb.hidden = true; img.removeAttribute('src'); document.body.style.overflow = '';
  };

  // True full screen (hides the browser's own toolbars). Not every browser allows it
  // for a page element (iPhone Safari doesn't), so the button only shows where it works.
  const canFull = document.fullscreenEnabled || document.webkitFullscreenEnabled;
  const isFull = () => !!(document.fullscreenElement || document.webkitFullscreenElement);
  const enterFull = () => {
    const req = (lb.requestFullscreen || lb.webkitRequestFullscreen).call(lb);
    if (req && req.catch) req.catch(() => {});  // refused: the viewer still works in the window
  };
  const exitFull = () => (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  const toggleFull = () => { if (canFull) isFull() ? exitFull() : enterFull(); };
  const fsBtn = lb.querySelector('.lb-fs');
  if (!canFull) fsBtn.hidden = true;
  fsBtn.onclick = e => { e.stopPropagation(); toggleFull(); };
  const syncFull = () => lb.classList.toggle('full', isFull());
  document.addEventListener('fullscreenchange', syncFull);
  document.addEventListener('webkitfullscreenchange', syncFull);

  // In full screen the controls fade out until the pointer moves.
  let idle;
  lb.addEventListener('pointermove', () => {
    lb.classList.remove('idle');
    clearTimeout(idle);
    idle = setTimeout(() => lb.classList.add('idle'), 2500);
  });

  figs.forEach((f, n) => f.addEventListener('click', () => open(n)));
  document.querySelector('.view-all').onclick = () => { open(0); if (canFull) enterFull(); };
  lb.querySelector('.lb-x').onclick = close;
  lb.querySelector('.lb-p').onclick = e => { e.stopPropagation(); show(i - 1); };
  lb.querySelector('.lb-n').onclick = e => { e.stopPropagation(); show(i + 1); };
  lb.addEventListener('click', e => { if (e.target === lb) close(); });
  addEventListener('keydown', e => {
    if (lb.hidden) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') show(i - 1);
    if (e.key === 'ArrowRight') show(i + 1);
    if (e.key === 'f' || e.key === 'F') toggleFull();
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
