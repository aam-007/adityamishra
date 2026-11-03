(() => {
  const links = document.querySelectorAll('a[aria-controls="contact-window"]');
  const window = document.getElementById('contact-window');
  if (!links.length || !window || typeof window.showModal !== 'function') return;
  let opener;
  links.forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    opener = link;
    window.showModal();
    document.body.classList.add('contact-is-open');
  }));
  window.addEventListener('close', () => {
    document.body.classList.remove('contact-is-open');
    opener?.focus();
  });
  window.addEventListener('click', event => {
    const bounds = window.getBoundingClientRect();
    if (event.target === window && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) window.close();
  });
})();
