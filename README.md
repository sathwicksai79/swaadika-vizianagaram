# SWAADIKA — Find What Tastes Right

> *Unfold the Flavours & Cuisines of Vizianagaram — From Morning Tiffins to Royal Dining & Evening Snacks.*

**SWAADIKA** is a hyper-local food discovery and restaurant comparison web platform tailored for Vizianagaram, Andhra Pradesh. Built with Flask and powered by Machine Learning, SWAADIKA helps food lovers discover curated dining spots, compare eatery menus side-by-side, and predict restaurant ratings using Random Forest models.

---

## Key Features

- **Hyper-Local Discovery:** Browse curated spots across three distinct categories:
  - 🌅 **Morning Tiffins:** Heritage tiffin centers, idli spots, and regional breakfast stops.
  - 🍽️ **Dining & Restaurants:** Multi-cuisine family restaurants, mandi houses, and fine dining.
  - ☕ **Evening Snacks & Cafés:** Street-side bites, bakeries, waffle shops, and cafés.
- **Side-by-Side Comparison:** Compare menus, average costs for two, ratings, and specialties between competing dining spots.
- **ML Rating Predictor:** Machine learning rating estimation built using scikit-learn's Random Forest algorithm trained on local restaurant parameters.
- **Direct Map Navigation:** Quick-link integrations to view and navigate to eateries across Vizianagaram on Google Maps.

---

## Tech Stack

- **Backend:** Python, Flask, Jinja2 Templates
- **Machine Learning & Data:** scikit-learn, pandas, numpy (Random Forest Regressor)
- **Frontend:** Responsive HTML5, CSS3, Vanilla JavaScript
- **Production Server:** Gunicorn

---

## Project Structure

```text
Swaadika_Project_01/
├── app.py                     # Flask application routes and API endpoints
├── train_model.py             # Script to train & save the Random Forest model
├── requirements.txt           # Python dependencies
├── data/                      # Local JSON datasets (restaurants, tiffins, snacks, menus)
├── model/                     # Trained ML model artifacts (.pkl)
├── static/                    # CSS stylesheets, JavaScript, and restaurant imagery
└── templates/                 # Jinja2 HTML templates