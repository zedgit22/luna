document.addEventListener('DOMContentLoaded', () => {
  const helpButton = document.getElementById('helpButton');
  if (!helpButton) {
    console.warn('Help button (#helpButton) not found.');
    return;
  }
  // Override any previously attached listeners to avoid duplicate tabs or wrong URL
  helpButton.onclick = (e) => {
    e.preventDefault();
    window.open('/static/help.html', '_blank', 'noopener');
  };
});document.addEventListener('DOMContentLoaded', () => {
  const helpButton = document.getElementById('helpButton');
  if (!helpButton) {
    console.warn('Help button (#helpButton) not found.');
    return;
  }
  // Override any previously attached listeners to avoid duplicate tabs or wrong URL
  helpButton.onclick = (e) => {
    e.preventDefault();
    window.open('/static/help.html', '_blank', 'noopener');
  };
});