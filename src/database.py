import os
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta
import uuid
import hashlib
import random
import string

CATEGORIES = ["TOP", "BOTTOM", "OUTER", "FOOTWEAR", "HIJAB"]

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")
images_dir = os.path.join(data_dir, "user_images")
users_csv = os.path.join(data_dir, "users.csv")

def initialize_db():
    os.makedirs(images_dir, exist_ok=True)
    if not os.path.exists(users_csv) or os.path.getsize(users_csv) == 0:
        df = pd.DataFrame(columns=["email", "username", "password_hash", "reset_token", "token_expiry"])
        df.to_csv(users_csv, index=False)
    else:
        df = pd.read_csv(users_csv)
        updated = False
        if "reset_token" not in df.columns:
            df["reset_token"] = None
            updated = True
        if "token_expiry" not in df.columns:
            df["token_expiry"] = None
            updated = True
        if updated:
            df.to_csv(users_csv, index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, username, password):
    initialize_db()
    df = pd.read_csv(users_csv)
    email = email.strip().lower()
    username = username.strip()
    
    if email in df['email'].astype(str).str.lower().values:
        return False, "Email already registered."
    if username.lower() in df['username'].astype(str).str.lower().values:
        return False, "Username already taken."
        
    new_user = {
        "email": email, "username": username, "password_hash": hash_password(password),
        "reset_token": None, "token_expiry": None
    }
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_csv(users_csv, index=False)
    return True, "Account created successfully!"

def authenticate_user(login_input, password):
    initialize_db()
    df = pd.read_csv(users_csv)
    login_input = login_input.strip().lower()
    
    df['email'] = df['email'].astype(str)
    df['username'] = df['username'].astype(str)
    
    user_row = df[(df['email'].str.lower() == login_input) | (df['username'].str.lower() == login_input)]
    
    if user_row.empty:
        return False, None, None
        
    stored_hash = user_row.iloc[0]['password_hash']
    if stored_hash == hash_password(password):
        return True, user_row.iloc[0]['username'], user_row.iloc[0]['email']
    return False, None, None

def generate_reset_token(email):
    initialize_db()
    df = pd.read_csv(users_csv)
    email = email.strip().lower()
    
    if email not in df['email'].astype(str).str.lower().values:
        return None
        
    token = ''.join(random.choices(string.digits, k=6))
    expiry = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    
    df.loc[df['email'].astype(str).str.lower() == email, 'reset_token'] = token
    df.loc[df['email'].astype(str).str.lower() == email, 'token_expiry'] = expiry
    df.to_csv(users_csv, index=False)
    return token

def reset_password(email, token, new_password):
    initialize_db()
    df = pd.read_csv(users_csv)
    email = email.strip().lower()
    
    user_row = df[df['email'].astype(str).str.lower() == email]
    if user_row.empty:
        return False, "Email not found."
        
    stored_token = str(user_row.iloc[0]['reset_token'])
    stored_expiry = user_row.iloc[0]['token_expiry']
    
    if stored_token != token:
        return False, "Invalid reset code."
        
    if pd.isna(stored_expiry) or datetime.now() > pd.to_datetime(stored_expiry):
        return False, "Reset code has expired. Please request a new one."
        
    df.loc[df['email'].astype(str).str.lower() == email, 'password_hash'] = hash_password(new_password)
    df.loc[df['email'].astype(str).str.lower() == email, 'reset_token'] = None
    df.loc[df['email'].astype(str).str.lower() == email, 'token_expiry'] = None
    df.to_csv(users_csv, index=False)
    return True, "Password reset successfully! You can now log in."

def get_user_files(email):
    safe_email = "".join(x for x in email if x.isalnum())
    closet_csv = os.path.join(data_dir, f"closet_{safe_email}.csv")
    history_csv = os.path.join(data_dir, f"history_{safe_email}.csv")
    
    if not os.path.exists(closet_csv):
        pd.DataFrame(columns=["item_id", "image_path", "category", "color", "name", "date_added"]).to_csv(closet_csv, index=False)
    if not os.path.exists(history_csv):
        pd.DataFrame(columns=["date", "weather", "temperature", "top_id", "bottom_id", "outer_id", "footwear_id", "hijab_id"]).to_csv(history_csv, index=False)
    return closet_csv, history_csv

# ---- Paste at the bottom of src/database.py ----

def get_closet(email):
    closet_csv, _ = get_user_files(email)
    return pd.read_csv(closet_csv, dtype=str)


def add_item(email, file, category, color, name):
    if file is None or not file.filename:
        return False, "Choose a photo first."
    if category not in CATEGORIES:
        return False, "Pick a valid category."
    try:
        img = Image.open(file.stream).convert("RGB")
    except Exception:
        return False, "That file isn't a readable image."
    img.thumbnail((800, 800))
    item_id = uuid.uuid4().hex[:8]
    filename = f"{item_id}.jpg"
    img.save(os.path.join(images_dir, filename), "JPEG", quality=85)

    closet_csv, _ = get_user_files(email)
    df = pd.read_csv(closet_csv, dtype=str)
    row = {"item_id": item_id, "image_path": filename, "category": category,
           "color": color.strip().lower(), "name": name.strip(),
           "date_added": datetime.now().strftime("%Y-%m-%d")}
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(closet_csv, index=False)
    return True, "Added to your closet."


def delete_item(email, item_id):
    closet_csv, _ = get_user_files(email)
    df = pd.read_csv(closet_csv, dtype=str)
    gone = df[df["item_id"].astype(str) == str(item_id)]
    for p in gone["image_path"].astype(str):
        path = os.path.join(images_dir, p)
        if os.path.exists(path):
            os.remove(path)
    df[df["item_id"].astype(str) != str(item_id)].to_csv(closet_csv, index=False)


def get_items_worn_last_3_days(email):
    _, history_csv = get_user_files(email)
    df = pd.read_csv(history_csv, dtype=str)
    if df.empty:
        return []
    cutoff = datetime.now() - timedelta(days=3)
    recent = df[pd.to_datetime(df["date"]) >= cutoff]
    id_cols = [c for c in df.columns if c.endswith("_id")]
    return [str(v) for v in recent[id_cols].values.ravel() if pd.notna(v)]


def save_outfit(email, weather, temperature, ids):
    _, history_csv = get_user_files(email)
    df = pd.read_csv(history_csv, dtype=str)
    row = {"date": datetime.now().strftime("%Y-%m-%d"), "weather": weather,
           "temperature": temperature}
    for cat in CATEGORIES:
        row[f"{cat.lower()}_id"] = ids.get(cat)
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(history_csv, index=False)


def get_weather_options():
    path = os.path.join(base_dir, "data", "processed", "weather_en.csv")
    if os.path.exists(path):
        return sorted(pd.read_csv(path)["Weather"].dropna().unique())
    return ["Sunny", "Cloudy", "Rainy", "Snowy"]

def get_history(email):
    """Returns {'YYYY-MM-DD': {'weather', 'temperature', 'items': [...]}} (last entry per day wins)."""
    closet = get_closet(email).drop_duplicates("item_id").set_index("item_id")
    _, history_csv = get_user_files(email)
    df = pd.read_csv(history_csv, dtype=str)
    order = ["HIJAB", "OUTER", "TOP", "BOTTOM", "FOOTWEAR"]
    out = {}
    for _, r in df.iterrows():
        items = []
        for cat in order:
            iid = r.get(f"{cat.lower()}_id")
            if pd.notna(iid) and iid in closet.index:
                it = closet.loc[iid]
                items.append({"category": cat, "name": it["name"], "color": it["color"],
                              "image_path": it["image_path"]})
        out[str(r["date"])[:10]] = {"weather": r["weather"],
                                    "temperature": r["temperature"], "items": items}
    return out