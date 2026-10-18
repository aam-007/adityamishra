(() => {
  const root = document.documentElement;
  let view = 'table';
  try { view = localStorage.getItem('research-view') === 'legacy' ? 'legacy' : 'table'; } catch (_) { /* Storage is optional. */ }
  root.dataset.researchView = view;
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('research-view-toggle');
    if (!button) return;
    const sync = () => {
      const legacy = root.dataset.researchView === 'legacy';
      button.textContent = legacy ? '[ Switch to Table Mode ]' : '[ Switch to Legacy Mode ]';
      button.setAttribute('aria-pressed', String(legacy));
      button.setAttribute('aria-label', legacy ? 'Legacy mode enabled; switch to table mode' : 'Enable legacy mode');
    };
    button.hidden = false;
    button.addEventListener('click', () => {
      const next = root.dataset.researchView === 'legacy' ? 'table' : 'legacy';
      root.dataset.researchView = next;
      try { localStorage.setItem('research-view', next); } catch (_) { /* Keep the current page usable. */ }
      sync();
    });
    sync();
  });
})();
