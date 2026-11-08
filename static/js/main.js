/* SWAADIKA shared frontend helpers. Page-specific behavior remains in each template. */

// Smooth scrolling for anchor links (e.g., #about)
document.addEventListener('click', (event) => {
  const link = event.target.closest('a[href^="#"]');
  if (!link) return;
  const targetId = link.getAttribute('href');
  if (targetId === '#' || !targetId) return;
  
  const target = document.querySelector(targetId);
  if (target) {
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});

/**
 * Shared rating prediction handler.
 * Replaces "Sattva Rating" with "Swaadika Rating" dynamically when users run predictions.
 */
async function predictRating(buttonElement, payload) {
  const card = buttonElement.closest('.place-card, .restaurant-card, .detail-container');
  const resultDisplay = card ? card.querySelector('.predicted-rating-value, .prediction-result') : null;

  try {
    buttonElement.disabled = true;
    buttonElement.textContent = 'Calculating...';

    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok && data.predicted_rating) {
      if (resultDisplay) {
        resultDisplay.innerHTML = `
          <div class="swaadika-badge" style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background: rgba(212, 175, 55, 0.15); border: 1px solid #d4af37; border-radius: 8px; color: #fdfcf7;">
            <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #d4af37; font-weight: 700;">Swaadika Rating:</span>
            <strong style="color: #e5a93c; font-size: 14px;">${data.predicted_rating} ★</strong>
          </div>
        `;
      }
    } else {
      if (resultDisplay) resultDisplay.textContent = 'Unable to predict';
    }
  } catch (err) {
    console.error('Prediction error:', err);
    if (resultDisplay) resultDisplay.textContent = 'Error predicting rating';
  } finally {
    buttonElement.disabled = false;
    buttonElement.textContent = 'Predict Rating';
  }
}