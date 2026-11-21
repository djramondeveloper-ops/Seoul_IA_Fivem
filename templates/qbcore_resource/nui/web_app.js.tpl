const app = document.getElementById('app');
const closeBtn = document.getElementById('closeBtn');

window.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.action === 'open') {
    app.classList.remove('hidden');
  }
});

closeBtn.addEventListener('click', async () => {
  app.classList.add('hidden');

  try {
    await fetch(`https://${GetParentResourceName()}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
  } catch (error) {
    console.error(error);
  }
});
