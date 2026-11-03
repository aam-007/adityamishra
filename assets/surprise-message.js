(() => {
  const data = document.getElementById('poetry-data');
  if (!data) return;
  const poems = JSON.parse(data.textContent);
  let previous = null;
  try { previous = sessionStorage.getItem('portfolio-last-poem'); } catch (_) { /* Storage is optional. */ }
  const choices = poems.filter(poem => poem.id !== previous);
  const poem = choices[Math.floor(Math.random() * choices.length)];
  document.getElementById('surprise-message').textContent = poem.text;
  document.getElementById('poem-author').textContent = '— ' + poem.author;
  const work = document.getElementById('poem-work');
  work.textContent = poem.title + (poem.excerpt ? ' (excerpt)' : '');
  work.href = poem.sourceUrl;
  document.querySelector('.poem blockquote').cite = poem.sourceUrl;
  try { sessionStorage.setItem('portfolio-last-poem', poem.id); } catch (_) { /* Storage is optional. */ }
})();
