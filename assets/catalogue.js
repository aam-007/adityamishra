(() => {
  const form = document.getElementById('filters');
  if (!form) return;
  const query = document.getElementById('query');
  const topic = document.getElementById('topic');
  const year = document.getElementById('year');
  const papers = [...document.querySelectorAll('#catalogue .paper')];
  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const entries = papers.map(element => ({ element, text: normalize(element.textContent + ' ' + (element.dataset.search || '')) }));
  const params = new URLSearchParams(location.search);
  query.value = params.get('q') || '';
  topic.value = params.get('topic') || '';
  year.value = params.get('year') || '';
  const update = () => {
    const terms = normalize(query.value.trim()).split(/\s+/).filter(Boolean);
    let count = 0;
    entries.forEach(({element, text}) => {
      const match = terms.every(term => text.includes(term)) && (!topic.value || element.dataset.topic === topic.value) && (!year.value || element.dataset.year === year.value);
      element.hidden = !match;
      if (match) count++;
    });
    document.getElementById('result-count').textContent = `${count} ${count === 1 ? 'document' : 'documents'}`;
    document.getElementById('empty').hidden = count !== 0;
    const state = new URLSearchParams();
    if (query.value.trim()) state.set('q', query.value.trim());
    if (topic.value) state.set('topic', topic.value);
    if (year.value) state.set('year', year.value);
    try { history.replaceState(null, '', location.pathname + (state.size ? '?' + state : '') + location.hash); } catch (_) { /* Filtering also works from local files. */ }
  };
  form.hidden = false;
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('reset', () => setTimeout(update, 0));
  update();
})();
