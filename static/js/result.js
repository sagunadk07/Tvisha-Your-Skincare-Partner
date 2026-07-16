window.addEventListener('load', () => {
  const target = window.RESULT_CONFIDENCE;

  setTimeout(() => { document.getElementById('conf-bar').style.width = target + '%'; }, 200);

  setTimeout(() => {
    document.querySelectorAll('.score-fill').forEach(el => { el.style.width = el.dataset.width + '%'; });
  }, 400);

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
    if (!hintHidden && Math.abs(pct - 50) > 3) { hint.classList.add('hidden'); hintHidden = true; }
  }

  viewport.addEventListener('mousedown', e => { dragging = true; setPos(e.clientX); e.preventDefault(); });
  document.addEventListener('mousemove', e => { if (dragging) setPos(e.clientX); });
  document.addEventListener('mouseup', () => { dragging = false; });
  viewport.addEventListener('touchstart', e => { dragging = true; setPos(e.touches[0].clientX); }, { passive: true });
  document.addEventListener('touchmove', e => { if (dragging) setPos(e.touches[0].clientX); }, { passive: true });
  document.addEventListener('touchend', () => { dragging = false; });
});
