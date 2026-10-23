(() => {
  const controls = document.querySelector('.sitemap-controls');
  const sections = [...document.querySelectorAll('.sitemap-tree details')];
  if (!controls) return;
  controls.hidden = false;
  document.getElementById('expand-map').addEventListener('click', () => sections.forEach(section => { section.open = true; }));
  document.getElementById('collapse-map').addEventListener('click', () => sections.forEach(section => { section.open = false; }));
})();
