document.querySelectorAll('[data-current-year]').forEach(element => {
  const year = String(new Date().getFullYear());
  element.textContent = year;
  element.dateTime = year;
  element.closest('.footer-year').hidden = false;
});
