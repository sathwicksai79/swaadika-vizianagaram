import os
import re
import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

def parse_price(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return None
    if isinstance(v, (int, float)): return float(v)
    nums = re.findall(r"\d+(?:\.\d+)?", str(v).replace(",", ""))
    return sum(float(x) for x in nums) / len(nums) if nums else None

def count_items(v):
    if not v or (isinstance(v, float) and pd.isna(v)): return 0
    if isinstance(v, list): return len(v)
    return len([x for x in str(v).split(",") if x.strip()])

# Now checking ALL THREE JSON files
DATASETS = [
    ("restaurants", "restaurants.json", "sattva_random_forest.pkl"),
    ("tiffins", "tiffins.json", "sattva_tiffins_random_forest.pkl"),
    ("snacks", "snacks.json", "sattva_snacks_random_forest.pkl")
]

for cat_name, filename, model_filename in DATASETS:
    json_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(json_path):
        print(f"Skipping {cat_name}: {filename} not found.")
        continue
        
    with open(json_path, "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    df_cat = pd.DataFrame(entries)
    if df_cat.empty:
        print(f"Skipping {cat_name}: {filename} is empty.")
        continue
        
    features_cat = pd.DataFrame({
        "price_for_two": df_cat["price_for_two"].apply(parse_price) if "price_for_two" in df_cat else None,
        "reviews": pd.to_numeric(df_cat["reviews"], errors="coerce") if "reviews" in df_cat else 0,
        "cuisine_count": df_cat["cuisines"].apply(count_items) if "cuisines" in df_cat else 0,
        "veg_dish_count": df_cat["veg_dishes"].apply(count_items) if "veg_dishes" in df_cat else 0,
        "nonveg_dish_count": df_cat["nonveg_dishes"].apply(count_items) if "nonveg_dishes" in df_cat else 0,
        "cuisines": df_cat["cuisines"].fillna("Unknown").astype(str) if "cuisines" in df_cat else "Unknown",
    })
    
    target_cat = pd.to_numeric(df_cat["rating"], errors="coerce") if "rating" in df_cat else pd.Series()
    mask_cat = target_cat.notna()

    if mask_cat.sum() >= 2:
        num_cols = ["price_for_two", "reviews", "cuisine_count", "veg_dish_count", "nonveg_dish_count"]
        cat_cols = ["cuisines"]
        
        preprocessor = ColumnTransformer([
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_cols),
            ("cat", Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="Unknown")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols)
        ])
        
        pipeline = Pipeline([("preprocessor", preprocessor), ("regressor", RandomForestRegressor(n_estimators=300, random_state=42))])
        pipeline.fit(features_cat.loc[mask_cat], target_cat.loc[mask_cat])
        
        joblib.dump({"pipeline": pipeline, "model_name": "Random Forest Regressor"}, os.path.join(MODEL_DIR, model_filename))
        print(f"Trained and saved {cat_name} model from {filename}.")
    else:
        print(f"Skipping {cat_name}: Not enough valid ratings to train a model.")