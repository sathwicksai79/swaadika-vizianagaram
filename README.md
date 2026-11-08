# SATTVA — Find What Tastes Right

SATTVA is a Flask food-discovery website focused on Vizianagaram, Andhra Pradesh. It preserves the existing restaurant Excel dataset and trained Random Forest model.

## Current navigation

Home → Explore → Tiffins / Restaurants / Evening Snacks → Shop details → Predict Rating (restaurant category only).

- The existing `data/updated_restaurent.xlsx` remains unchanged.
- The existing `model/sattva_random_forest.pkl` remains unchanged.
- The existing restaurant model is used only for the restaurant category. Tiffins and snacks intentionally do not show invented predictions.
- `data/tiffins.json` and `data/snacks.json` start empty because the uploaded project contains no verified tiffin-shop or snack-shop dataset. Category pages show an honest empty state until verified records are added.
- Addresses and delivery availability are not present in the current restaurant spreadsheet, so the site explicitly labels them unavailable rather than guessing.
- Existing `/restaurant/<id>`, `/compare`, `/api/predict/<id>` and `/api/restaurants` endpoints are preserved for compatibility.

## Adding verified tiffin or snack shops

Add records to `data/tiffins.json` or `data/snacks.json`. Each file must be a JSON array. Example record structure (replace all example values with verified details before using):

```json
[
  {
    "name": "Verified shop name",
    "address": "Verified address or locality",
    "food_type": "Idli, dosa, vada",
    "price_range": "₹30–₹100",
    "price_for_two": 100,
    "famous_dishes": "Idli, dosa, vada",
    "image": "optional-existing-image-filename.jpeg",
    "delivery": null
  }
]
```

Use the `famous_dishes` field for the category's food highlights. `image` should be a filename that actually exists in `static/images/`; leave it blank if no matching image is available. `delivery` can be `true`, `false`, or `null` (unknown). Do not add unverified shop data. These files are for discovery only; the restaurant model is not applied to them.

## Run

Activate your existing virtual environment, then from the `sattvaa` project folder:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

To retrain the restaurant model only if you intentionally want to do so:

```bash
python train_model.py
```

The model and source dataset were not overwritten during these website changes.
