from flask import Flask, render_template, jsonify, request, abort, redirect, url_for
import os
import re
import json
import joblib
import pandas as pd

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATHS = {
    "restaurants": os.path.join(MODEL_DIR, "sattva_random_forest.pkl"),
    "tiffins": os.path.join(MODEL_DIR, "sattva_tiffins_random_forest.pkl"),
    "snacks": os.path.join(MODEL_DIR, "sattva_snacks_random_forest.pkl"),
}

# ==================================================
# AMBIENCE & MENU IMAGE MAPPINGS
# ==================================================

AMBIENCE_MAP = {
    "Happy Restaurant": ["happy_amb1.jpeg", "happy_amb2.jpeg"],
    "Sunny Restaurant": ["sunny_amb1.jpeg"],
}

MENU_MAP = {
    "Happy Restaurant": ["happy_menu1.jpeg", "happy_menu2.jpeg"],
    "Sunny Restaurant": ["sunny_menu1.jpeg"],
}

# ==================================================
# DIGITAL MENU LOADER & NAME NORMALIZER
# ==================================================

def normalize_restaurant_name(text):
    """Normalizes restaurant names by handling quotes, lowercase, and symbols."""
    if not text:
        return ""
    # Convert curly quotes to straight, lowercase, remove punctuation and spaces
    cleaned = str(text).lower().replace("’", "'").replace("`", "'")
    return re.sub(r"[^a-z0-9]", "", cleaned)

def get_restaurant_menu(restaurant_name):
    """Loads and retrieves the menu for a restaurant from data/menus.json."""
    menus_file = os.path.join(DATA_DIR, "menus.json")
    if not os.path.exists(menus_file):
        return None

    try:
        with open(menus_file, "r", encoding="utf-8") as file:
            all_menus = json.load(file)

        target = normalize_restaurant_name(restaurant_name)
        for key, menu in all_menus.items():
            if normalize_restaurant_name(key) == target:
                return menu
    except Exception as e:
        app.logger.warning("Could not load menu for %s: %s", restaurant_name, e)
        return None

    return None

# ==================================================
# GENERAL HELPER FUNCTIONS
# ==================================================

def is_missing(value):
    if value is None or value == "":
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False

def parse_price(value):
    if is_missing(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    numbers = re.findall(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    values = [float(number) for number in numbers]
    return sum(values) / len(values) if values else None

def count_items(value):
    if is_missing(value) or not str(value).strip():
        return 0
    return len([item for item in str(value).split(",") if item.strip()])

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")

# ==================================================
# UNIFIED JSON DATA LOADER
# ==================================================

def load_category_data(filename, category):
    path = os.path.join(DATA_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as file:
            entries = json.load(file)
    except (OSError, json.JSONDecodeError):
        app.logger.warning("Could not load %s", path)
        return []

    if not isinstance(entries, list):
        app.logger.warning("%s must contain a JSON list.", filename)
        return []

    clean = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        name_value = entry.get("name")
        if is_missing(name_value) or not str(name_value).strip():
            continue

        name = str(name_value).strip()
        food_type = entry.get("food_type") or entry.get("cuisines") or "Food type not provided"
        price_range = entry.get("price_range") or entry.get("price_text") or ""
        price_for_two = entry.get("price_for_two") or entry.get("price")
        
        price = parse_price(price_for_two) if not is_missing(price_for_two) else parse_price(price_range)

        try:
            rating = round(float(entry.get("rating")), 1) if not is_missing(entry.get("rating")) else None
        except (ValueError, TypeError):
            rating = None

        try:
            reviews = int(float(entry.get("reviews"))) if not is_missing(entry.get("reviews")) else None
        except (ValueError, TypeError):
            reviews = None

        if rating is not None and rating > 5.0 and (reviews is None or reviews <= 5):
            rating, reviews = (reviews if reviews is not None else 4.5), int(rating)

        clean.append({
            "id": len(clean),
            "name": name,
            "slug": slugify(name),
            "category": category,
            "cuisines": str(food_type),
            "address": str(entry.get("address") or ""),
            "price": price,
            "price_for_two": price,
            "price_text": str(price_range),
            "price_range": str(price_range),
            "rating": rating,
            "reviews": reviews,
            "veg_dishes": str(entry.get("famous_dishes") or entry.get("veg_dishes") or ""),
            "nonveg_dishes": str(entry.get("nonveg_dishes") or ""),
            "image": str(entry.get("image") or ""),
            "delivery": entry.get("delivery"),
            "ambience_images": AMBIENCE_MAP.get(name, []),
            "menu_images": MENU_MAP.get(name, []),
        })

    return clean

shops_by_category = {
    "restaurants": load_category_data("restaurants.json", "restaurants"),
    "tiffins": load_category_data("tiffins.json", "tiffins"),
    "snacks": load_category_data("snacks.json", "snacks"),
}
restaurants = shops_by_category["restaurants"]

# ==================================================
# CATEGORY CONFIGURATION
# ==================================================

CATEGORY_INFO = {
    "restaurants": {
        "label": "Restaurants",
        "eyebrow": "DINING & MULTI-CUISINE",
        "description": "Family dining, biryani centers, and multi-cuisine restaurants across Vizianagaram.",
        "symbol": "✦",
        "tone": "restaurant",
        "image": "categories/cat_restaurants.png",
    },
    "tiffins": {
        "label": "Tiffins",
        "eyebrow": "BREAKFAST & MORNING SPECIALS",
        "description": "Fresh South Indian breakfast, tiffin centers, and daily morning meals.",
        "symbol": "☀",
        "tone": "tiffin",
        "image": "categories/cat_tiffins.png",
    },
    "snacks": {
        "label": "Evening Snacks",
        "eyebrow": "EVENING BITES & QUICK EATS",
        "description": "Local chaat, fast food, and popular evening refreshment spots.",
        "symbol": "☕",
        "tone": "snack",
        "image": "categories/cat_snacks.png",
    },
}

# ==================================================
# LOAD ML MODELS
# ==================================================

def load_model_file(path):
    if not os.path.exists(path):
        app.logger.warning("ML model not found: %s", path)
        return None
    try:
        saved_model = joblib.load(path)
        if isinstance(saved_model, dict):
            pipeline = saved_model.get("pipeline") or saved_model.get("model")
            if pipeline is None:
                app.logger.error("No pipeline or model found in %s", path)
                return None
            name = saved_model.get("model_name", "Random Forest Regressor")
        else:
            pipeline = saved_model
            name = "Random Forest Regressor"

        if not callable(getattr(pipeline, "predict", None)):
            app.logger.error("Model has no predict method: %s", path)
            return None

        return {"pipeline": pipeline, "model_name": name}
    except Exception:
        app.logger.exception("Could not load model: %s", path)
        return None

category_models = {category: load_model_file(path) for category, path in MODEL_PATHS.items()}

# ==================================================
# RATINGS PREDICTOR
# ==================================================

def prepare_features(shop, overrides=None):
    overrides = overrides or {}
    price = overrides.get("price_for_two", shop.get("price"))
    reviews = overrides.get("reviews", shop.get("reviews"))

    try:
        price = float(price) if price not in (None, "") else None
    except (ValueError, TypeError):
        price = None

    try:
        reviews = float(reviews) if reviews not in (None, "") else None
    except (ValueError, TypeError):
        reviews = None

    cuisines = shop.get("cuisines") or "Unknown"

    return pd.DataFrame([{
        "price_for_two": price,
        "reviews": reviews,
        "cuisine_count": count_items(cuisines),
        "veg_dish_count": count_items(shop.get("veg_dishes", "")),
        "nonveg_dish_count": count_items(shop.get("nonveg_dishes", "")),
        "cuisines": cuisines,
    }])

def get_prediction(shop, overrides=None, category=None):
    category = category or shop.get("category", "restaurants")
    selected_model = category_models.get(category)
    if not selected_model:
        raise RuntimeError(f"No trained prediction model is available for the '{category}' category.")
    
    features = prepare_features(shop, overrides)
    prediction = float(selected_model["pipeline"].predict(features)[0])
    return round(max(1.0, min(5.0, prediction)), 2)

def validate_prediction_inputs():
    price_raw = request.form.get("price_for_two", "").strip()
    reviews_raw = request.form.get("reviews", "").strip()

    price = float(price_raw) if price_raw else None
    reviews = float(reviews_raw) if reviews_raw else None

    if price is not None and not 0 <= price <= 100000:
        raise ValueError("Price must be between ₹0 and ₹100,000.")
    if reviews is not None and not 0 <= reviews <= 100000000:
        raise ValueError("Review count must be between 0 and 100,000,000.")
    if reviews is not None and not reviews.is_integer():
        raise ValueError("Review count must be a whole number.")

    return price, reviews

def find_shop(category, shop_id):
    if category not in shops_by_category:
        abort(404)
    shops = shops_by_category[category]
    if shop_id < 0 or shop_id >= len(shops):
        abort(404)
    return shops[shop_id]

# ==================================================
# ROUTES
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/explore")
def explore():
    return render_template("explore.html", categories=CATEGORY_INFO)

@app.route("/category/<category>")
def category_listing(category):
    if category not in CATEGORY_INFO:
        abort(404)
    return render_template("category.html", category=CATEGORY_INFO[category], category_key=category, shops=shops_by_category[category])

@app.route("/shop/<category>/<int:shop_id>")
def shop_details(category, shop_id):
    shop = find_shop(category, shop_id)
    auto_prediction = None
    selected_model = category_models.get(category)

    if selected_model:
        try:
            auto_prediction = get_prediction(shop, category=category)
        except Exception:
            app.logger.exception("Automatic prediction failed for %s", category)

    # Load digital menu only for restaurants
    menu_data = None
    if category == "restaurants":
        menu_data = get_restaurant_menu(shop.get("name"))

    return render_template(
        "restaurant.html",
        restaurant=shop,
        category=CATEGORY_INFO[category],
        category_key=category,
        model_available=bool(selected_model),
        auto_prediction=auto_prediction,
        menu_data=menu_data,
    )

@app.route("/restaurant/<int:restaurant_id>")
def restaurant_details(restaurant_id):
    if restaurant_id < 0 or restaurant_id >= len(restaurants):
        abort(404)
    return redirect(url_for("shop_details", category="restaurants", shop_id=restaurant_id))

@app.route("/predict/<category>/<int:shop_id>", methods=["GET", "POST"])
def predict_page(category, shop_id):
    shop = find_shop(category, shop_id)
    result = None
    error = None
    selected_model = category_models.get(category)

    if request.method == "POST":
        if not selected_model:
            error = "A trained rating-prediction model is not available for this category yet. Please check the category model file and training data."
        else:
            try:
                price, reviews = validate_prediction_inputs()
                overrides = {
                    "price_for_two": price if price is not None else shop.get("price"),
                    "reviews": reviews if reviews is not None else shop.get("reviews"),
                }
                result = {
                    "predicted_rating": get_prediction(shop, overrides, category=category),
                    "current_rating": shop.get("rating"),
                    "model_name": selected_model["model_name"],
                    "price": overrides["price_for_two"],
                    "reviews": overrides["reviews"],
                }
            except (ValueError, TypeError):
                error = "Enter a valid non-negative price and review count."
            except Exception:
                app.logger.exception("Prediction failed for %s", category)
                error = "Prediction could not be generated. Please check the trained model."

    return render_template("predict.html", restaurant=shop, category=CATEGORY_INFO[category], category_key=category, result=result, error=error, model_available=bool(selected_model))

@app.route("/compare")
def compare():
    return render_template("compare.html", restaurants=restaurants)

@app.route("/api/predict/<int:restaurant_id>", methods=["GET", "POST"])
def predict_api(restaurant_id):
    if restaurant_id < 0 or restaurant_id >= len(restaurants):
        return jsonify({"success": False, "error": "Restaurant not found"}), 404
    
    shop = restaurants[restaurant_id]
    if not category_models.get("restaurants"):
        return jsonify({"success": False, "error": "Restaurant prediction model is unavailable"}), 503

    try:
        overrides = {}
        if request.method == "POST":
            body = request.get_json(silent=True) or request.form
            for key in ("price_for_two", "reviews"):
                value = body.get(key)
                if value not in (None, ""):
                    number = float(value)
                    maximum = 100000 if key == "price_for_two" else 100000000
                    if number < 0 or number > maximum:
                        raise ValueError(f"Invalid {key}")
                    if key == "reviews" and not number.is_integer():
                        raise ValueError("Review count must be a whole number")
                    overrides[key] = number

        predicted = get_prediction(shop, overrides, category="restaurants")
        return jsonify({
            "success": True,
            "predicted_rating": predicted,
            "current_rating": shop["rating"],
            "model_name": category_models["restaurants"]["model_name"],
            "cuisines": shop["cuisines"],
            "veg_dishes": shop["veg_dishes"],
            "nonveg_dishes": shop["nonveg_dishes"],
            "delivery": shop["delivery"],
        })
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid prediction inputs"}), 400
    except Exception:
        app.logger.exception("Restaurant prediction API failed")
        return jsonify({"success": False, "error": "Prediction could not be generated"}), 500

@app.route("/api/restaurants")
def api_restaurants():
    return jsonify(restaurants)

@app.route("/api/model-status")
def model_status():
    return jsonify({
        category: {
            "available": bool(category_models.get(category)),
            "model_name": category_models[category]["model_name"] if category_models.get(category) else None,
            "shops_loaded": len(shops_by_category.get(category, [])),
        }
        for category in CATEGORY_INFO
    })

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)