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
    if not os.path.exists(users_csv):
        df = pd.DataFrame(columns=["email", "username", "password_hash", "reset_token", "token_expiry"])
        df.to_csv(users_csv, index=False)
    else:
        # تأكد بلي الأعمدة الجديدة كاينة، وإلا زيدهم (باش ماتبانش مشاكل مع الملفات القديمة)
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
    
    if email in df['email'].values:
        return False, "Email already registered."
    if username.lower() in df['username'].str.lower().values:
        return False, "Username already taken."
        
    new_user = {
        "email": email, "username": username, "password_hash": hash_password(password),
        "reset_token": None, "token_expiry": None
    }
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_csv(users_csv, index=False)
    return True, "Account created successfully!"

def authenticate_user(login_input, password):
    """يقبل الإيميل أو اسم المستخدم"""
    initialize_db()
    df = pd.read_csv(users_csv)
    login_input = login_input.strip().lower()
    
    user_row = df[(df['email'] == login_input) | (df['username'].str.lower() == login_input)]
    
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
    
    if email not in df['email'].values:
        return None
        
    token = ''.join(random.choices(string.digits, k=6))
    expiry = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    
    df.loc[df['email'] == email, 'reset_token'] = token
    df.loc[df['email'] == email, 'token_expiry'] = expiry
    df.to_csv(users_csv, index=False)
    return token

def reset_password(email, token, new_password):
    initialize_db()
    df = pd.read_csv(users_csv)
    email = email.strip().lower()
    
    user_row = df[df['email'] == email]
    if user_row.empty:
        return False, "Email not found."
        
    stored_token = str(user_row.iloc[0]['reset_token'])
    stored_expiry = user_row.iloc[0]['token_expiry']
    
    if stored_token != token:
        return False, "Invalid reset code."
        
    if pd.isna(stored_expiry) or datetime.now() > pd.to_datetime(stored_expiry):
        return False, "Reset code has expired. Please request a new one."
        
    df.loc[df['email'] == email, 'password_hash'] = hash_password(new_password)
    df.loc[df['email'] == email, 'reset_token'] = None
    df.loc[df['email'] == email, 'token_expiry'] = None
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

def add_item(email, image_file, category, color, name):
    closet_csv, _ = get_user_files(email)
    item_id = str(uuid.uuid4())[:8]
    image_filename = f"{item_id}.jpg"
    image_path = os.path.join(images_dir, image_filename)
    
    if isinstance(image_file, Image.Image):
        image_obj = image_file.convert("RGB")
    else:
        image_obj = Image.open(image_file).convert("RGB")
    image_obj.save(image_path, "JPEG")
    
    df = pd.read_csv(closet_csv)
    new_row = {
        "item_id": item_id, "image_path": image_path, "category": category.upper(),
        "color": color.strip().lower(), "name": name.strip(),
        "date_added": datetime.now().strftime("%Y-%m-%d")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(closet_csv, index=False)
    return item_id

def get_closet(email):
    closet_csv, _ = get_user_files(email)
    return pd.read_csv(closet_csv)

def save_outfit_to_calendar(email, weather, temperature, top_id, bottom_id, outer_id, footwear_id, hijab_id=None):
    _, history_csv = get_user_files(email)
    df = pd.read_csv(history_csv)
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"), "weather": weather,
        "temperature": temperature, "top_id": top_id, "bottom_id": bottom_id,
        "outer_id": outer_id, "footwear_id": footwear_id, "hijab_id": hijab_id
    }
    df = df[df["date"] != new_entry["date"]]
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(history_csv, index=False)

def get_items_worn_last_3_days(email):
    _, history_csv = get_user_files(email)
    df = pd.read_csv(history_csv)
    if df.empty: return []
    three_days_ago = datetime.now() - timedelta(days=3)
    df["date"] = pd.to_datetime(df["date"])
    recent_df = df[df["date"] >= three_days_ago]
    recent_ids = []
    for col in ["top_id", "bottom_id", "outer_id", "footwear_id", "hijab_id"]:
        if col in recent_df.columns:
            recent_ids.extend(recent_df[col].dropna().tolist())
    return list(set(recent_ids))

def get_item_by_id(email, item_id):
    df = get_closet(email)
    match = df[df["item_id"] == item_id]
    if not match.empty: return match.iloc[0].to_dict()
    return None