document.addEventListener('click', function (event) {
  const row = event.target.closest('tr[data-href]');
  if (row && !event.target.closest('a, button, input') && !window.getSelection().toString()) {
    window.location.href = row.dataset.href;
  }
});
