import os
import sys
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
import database
import recommender

def reset_database():
    """Wipes the database clean so we can start fresh for testing."""
    if os.path.exists(database.closet_csv):
        os.remove(database.closet_csv)
    if os.path.exists(database.history_csv):
        os.remove(database.history_csv)
    database.initialize_db()
    print("🧹 Database reset.")

def add_dummy_item(category, color, name):
    """Adds a dummy item with a blank image to the closet."""
    # Create a tiny blank white image
    img = Image.new('RGB', (100, 100), color = 'white')
    item_id = database.add_item(img, category, color, name)
    return item_id

print("--- 1. Setting up Dummy Closet ---")
reset_database()

# Add clothes
top_white = add_dummy_item("TOP", "white", "White Shirt")
top_black = add_dummy_item("TOP", "black", "Black Shirt")
bottom_blue = add_dummy_item("BOTTOM", "blue", "Blue Jeans")
bottom_red = add_dummy_item("BOTTOM", "red", "Red Mini Skirt") # Should be filtered out by modesty rule
outer_brown = add_dummy_item("OUTER", "brown", "Winter Coat")
shoes = add_dummy_item("FOOTWEAR", "white", "Sneakers")
hijab_blue = add_dummy_item("HIJAB", "blue", "Blue Hijab")
hijab_beige = add_dummy_item("HIJAB", "beige", "Beige Hijab")

print(f"✅ Added 8 items to the closet.")

print("\n--- 2. Setting up Fake History ---")
# Let's pretend the user wore the White Shirt and Blue Jeans 2 days ago.
# We do this by manually writing to the history CSV.
history_df = pd.read_csv(database.history_csv)
fake_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
fake_entry = {
    "date": fake_date,
    "weather": "Sunny",
    "temperature": 25,
    "top_id": top_white,
    "bottom_id": bottom_blue,
    "outer_id": None,
    "footwear_id": shoes,
    "hijab_id": None
}
history_df = pd.concat([history_df, pd.DataFrame([fake_entry])], ignore_index=True)
history_df.to_csv(database.history_csv, index=False)
print(f"✅ Faked history: Wore White Shirt and Blue Jeans on {fake_date}")

print("\n" + "="*50)
print("--- 3. TESTING THE AI BRAIN ---")
print("="*50)

# TEST 1: Cold and Rainy (Needs Jacket)
print("\nTEST 1: Rainy and 10°C (Cold)")
res = recommender.get_outfit_recommendation("Rainy", 10)
for cat, item in res["outfit"].items():
    if item:
        print(f"  {cat}: {item['name']} ({item['color']}) | Warning: {item['warning']}")
    else:
        print(f"  {cat}: None")
print(f"  Messages: {res['messages']}")

# TEST 2: Hot and Sunny (No Jacket needed)
print("\nTEST 2: Sunny and 32°C (Hot)")
res = recommender.get_outfit_recommendation("Sunny", 32)
for cat, item in res["outfit"].items():
    if item:
        print(f"  {cat}: {item['name']} ({item['color']}) | Warning: {item['warning']}")
    else:
        print(f"  {cat}: None")
print(f"  Messages: {res['messages']}")

# TEST 3: Empty Closet Warning (Delete all items)
print("\nTEST 3: Empty Closet")
reset_database() # Wipes it clean
res = recommender.get_outfit_recommendation("Sunny", 20)
print(f"  Result: {res.get('error')}")