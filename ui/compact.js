/* Layout overlay — injected by server.py, index.html untouched.
 * Once a check starts, the intro and the example chips fold away and the page scrolls to
 * the verdict, so the result is on screen instead of below the fold. Clearing the
 * textarea brings the intro back. */
(function () {
  'use strict';
  const css = document.createElement('style');
  css.textContent = `
    body.compact .hero, body.compact .box .ex { display: none; }
    body.compact .box textarea { min-height: 64px; }
  `;
  document.head.appendChild(css);

  function init() {
    const verdict = document.getElementById('s-verdict');
    const claim = document.getElementById('claim');
    if (!verdict) return;
    let wasHidden = verdict.classList.contains('hidden');
    new MutationObserver(() => {
      const hidden = verdict.classList.contains('hidden');
      if (wasHidden && !hidden) {
        document.body.classList.add('compact');
        requestAnimationFrame(() => verdict.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      }
      wasHidden = hidden;
    }).observe(verdict, { attributes: true, attributeFilter: ['class'] });
    if (claim) claim.addEventListener('input', () => {
      if (!claim.value.trim() && verdict.classList.contains('hidden')) document.body.classList.remove('compact');
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
