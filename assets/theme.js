(() => {
  let theme = 'paper';
  try { theme = localStorage.getItem('theme') || 'paper'; } catch (_) { /* Storage is optional. */ }
  document.documentElement.dataset.theme = theme === 'terminal' ? 'terminal' : 'paper';
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    const sync = () => {
      const terminal = document.documentElement.dataset.theme === 'terminal';
      document.body.classList.toggle('retro-dark', terminal);
      button.textContent = terminal ? '[ Switch to Paper Mode ]' : '[ Switch to Terminal Mode ]';
      button.setAttribute('aria-pressed', String(terminal));
      button.setAttribute('aria-label', terminal ? 'Terminal mode enabled; switch to paper mode' : 'Enable terminal mode');
    };
    button.hidden = false;
    button.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'terminal' ? 'paper' : 'terminal';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('theme', next); } catch (_) { /* Keep the current session usable. */ }
      sync();
    });
    sync();
  });
})();
