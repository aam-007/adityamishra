(() => {
  const link = document.getElementById('contact-open');
  const window = document.getElementById('contact-window');
  if (!link || !window || typeof window.showModal !== 'function') return;
  link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    window.showModal();
    document.body.classList.add('contact-is-open');
  });
  window.addEventListener('close', () => {
    document.body.classList.remove('contact-is-open');
    link.focus();
  });
  window.addEventListener('click', event => {
    const bounds = window.getBoundingClientRect();
    if (event.target === window && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) window.close();
  });
})();
