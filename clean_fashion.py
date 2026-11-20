import os
import pandas as pd

# 1. Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(base_dir, "data", "raw", "fashion", "styles.csv")
output_path = os.path.join(base_dir, "data", "processed", "fashion_clean.csv")

# Ensure processed folder exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print("Loading raw data...")
fashion = pd.read_csv(input_path, on_bad_lines="skip")

# 2. Keep only Apparel and Footwear
print("Filtering categories...")
fashion = fashion[fashion["masterCategory"].isin(["Apparel", "Footwear"])]

# Drop rows missing crucial data
fashion = fashion.dropna(subset=["subCategory", "articleType", "baseColour"])

# Normalize strings (lowercase, strip spaces)
for col in ["subCategory", "articleType", "baseColour"]:
    fashion[col] = fashion[col].astype(str).str.strip().str.lower()

# 3. Create the Mapping Function
def map_to_internal_category(row):
    sub = row["subCategory"]
    art = row["articleType"]
    master = row["masterCategory"]

    if master == "Footwear":
        return "FOOTWEAR"
    
    # Check for Outerwear
    if art in ["jackets", "blazers", "sweatshirts", "sweaters", "rain jacket", "coat"]:
        return "OUTER"
    
    # Check Topwear (using subCategory is safer)
    if sub == "topwear":
        return "TOP"
    
    # Check Bottomwear
    if sub == "bottomwear":
        return "BOTTOM"
    
    # Everything else (innerwear, loungewear, dresses, etc.) gets dropped for now
    return None

print("Mapping to internal categories...")
fashion["internal_category"] = fashion.apply(map_to_internal_category, axis=1)

# Drop items that didn't map to our 4 categories
fashion = fashion.dropna(subset=["internal_category"])

# 4. Show the results
print("\n✅ Cleaned Data Shape:", fashion.shape)
print("\n--- Internal Categories ---")
print(fashion["internal_category"].value_counts())

# 5. Save the cleaned data
fashion.to_csv(output_path, index=False)
print(f"\nSaved cleaned dataset to: {output_path}")