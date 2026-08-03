window.addEventListener('load', () => {
  const target = window.RESULT_CONFIDENCE;

  setTimeout(() => { document.getElementById('conf-bar').style.width = target + '%'; }, 200);

  setTimeout(() => {
    document.querySelectorAll('.score-fill').forEach(el => { el.style.width = el.dataset.width + '%'; });
  }, 400);

  const revealTargets = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealTargets.length) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealTargets.forEach(el => observer.observe(el));
  } else {
    revealTargets.forEach(el => el.classList.add('is-visible'));
  }

  const viewport = document.getElementById('comp-viewport');
  if (!viewport) return;

  const original = document.getElementById('comp-original');
  const handle   = document.getElementById('comp-handle');
  const hint     = document.getElementById('comp-hint');
  let dragging = false, hintHidden = false;

  function setPos(clientX) {
    const rect = viewport.getBoundingClientRect();
    let pct = (clientX - rect.left) / rect.width * 100;
    pct = Math.max(1, Math.min(99, pct));
    original.style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
    handle.style.left = pct + '%';
    viewport.setAttribute('aria-valuenow', Math.round(pct));
    if (!hintHidden && Math.abs(pct - 50) > 3) { hint.classList.add('hidden'); hintHidden = true; }
  }

  viewport.addEventListener('mousedown', e => { dragging = true; setPos(e.clientX); e.preventDefault(); });
  document.addEventListener('mousemove', e => { if (dragging) setPos(e.clientX); });
  document.addEventListener('mouseup', () => { dragging = false; });
  viewport.addEventListener('touchstart', e => { dragging = true; setPos(e.touches[0].clientX); }, { passive: true });
  document.addEventListener('touchmove', e => { if (dragging) setPos(e.touches[0].clientX); }, { passive: true });
  document.addEventListener('touchend', () => { dragging = false; });

  viewport.addEventListener('keydown', e => {
    const current = parseFloat(viewport.getAttribute('aria-valuenow')) || 50;
    if (e.key === 'ArrowLeft') { setPos(viewport.getBoundingClientRect().left + viewport.getBoundingClientRect().width * (current - 5) / 100); e.preventDefault(); }
    else if (e.key === 'ArrowRight') { setPos(viewport.getBoundingClientRect().left + viewport.getBoundingClientRect().width * (current + 5) / 100); e.preventDefault(); }
  });
});
