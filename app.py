import streamlit as st
import os
import sys
import pandas as pd
from PIL import Image

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
import database
import recommender
import email_utils

# 1. إعدادات الصفحة والتصميم (CSS احترافي)
st.set_page_config(page_title="Smart Closet", page_icon="👗", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .block-container {
        max-width: 500px !important; padding-top: 2rem !important;
        background-color: white; border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        padding-bottom: 2rem !important; margin-top: 2rem;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3em;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white; font-weight: bold; border: none; transition: 0.3s;
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.4); 
    }
    .stTextInput>div>div>input { border-radius: 10px; border: 1px solid #dfe6e9; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 10px; background-color: #f1f2f6; }
    .stTabs [aria-selected="true"] { background-color: #6c5ce7; color: white; }
    
    /* ستايل خاص بالأزرار الكبار (Cards) */
    div[data-testid="stVerticalBlock"] div.stButton > button {
        height: 4em;
        font-size: 1.1em;
        text-align: left;
        padding-left: 20px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

database.initialize_db()

# 2. إدارة الحالة (Session State)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.username = ""
    st.session_state.page = "Home" # الصفحة الافتراضية

# ==========================================
# 1. LOGIN PAGE
# ==========================================
if not st.session_state.logged_in:
    st.title("👗 Smart Closet")
    st.markdown("<p style='text-align: center; color: gray;'>Your Personal AI Stylist</p>", unsafe_allow_html=True)
    
    login_tab, signup_tab, forgot_tab = st.tabs(["Log In", "Sign Up", "Forgot Password"])
    
    with login_tab:
        with st.form("login_form"):
            login_input = st.text_input("Email or Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In")
            
            if submit:
                success, username, user_email = database.authenticate_user(login_input, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.email = user_email
                    st.session_state.username = username
                    st.session_state.page = "Home" # بعد الدخول يمشي للرئيسية
                    st.rerun()
                else:
                    st.error("❌ Incorrect email/username or password.")
                    
    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("Email Address")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            signup_submit = st.form_submit_button("Create Account")
            
            if signup_submit:
                if new_email and new_username and new_password:
                    success, message = database.register_user(new_email, new_username, new_password)
                    if success: st.success(message + " Please log in.")
                    else: st.error(message)
                else:
                    st.warning("Please fill all fields.")
                    
    with forgot_tab:
        st.write("Enter your email to receive a 6-digit reset code.")
        forgot_email = st.text_input("Registered Email")
        
        if st.button("Send Reset Code"):
            token = database.generate_reset_token(forgot_email)
            if token:
                email_sent = email_utils.send_reset_email(forgot_email, token)
                if email_sent: st.success("✅ Code sent! Check your inbox.")
                else:
                    st.warning("⚠️ Email not configured. Code printed in terminal.")
                    print(f"--- RESET TOKEN for {forgot_email}: {token} ---")
            else:
                st.error("❌ Email not found.")
                
        st.divider()
        with st.form("reset_form"):
            reset_email = st.text_input("Your Email", key="reset_email_input")
            reset_code = st.text_input("6-Digit Code")
            new_pass = st.text_input("New Password", type="password")
            reset_submit = st.form_submit_button("Reset Password")
            
            if reset_submit:
                success, msg = database.reset_password(reset_email, reset_code, new_pass)
                if success: st.success(msg)
                else: st.error(msg)
                    
    st.stop()

# ==========================================
# 2. MAIN APP (Navigation System)
# ==========================================
# شريط جانبي فيه معلومات المستخدم وزر الخروج
with st.sidebar:
    st.title(f"👋 {st.session_state.username}")
    st.write(f"📧 {st.session_state.email}")
    st.divider()
    if st.button("🚪 Log Out"):
        st.session_state.logged_in = False
        st.session_state.page = "Home"
        st.rerun()

# ----------------- الصفحة الرئيسية (Home) -----------------
if st.session_state.page == "Home":
    st.title(f"Hello, {st.session_state.username}! ✨")
    st.write("What would you like to do today?")
    st.divider()
    
    # أزرار التنقل
    if st.button("📸 Shoot Station\n\nAdd new clothes to your wardrobe"):
        st.session_state.page = "Shoot"
        st.rerun()
        
    if st.button("👗 My Wardrobe\n\nView and manage your clothes"):
        st.session_state.page = "Wardrobe"
        st.rerun()
        
    if st.button("🌤️ AI Stylist\n\nGenerate an outfit based on the weather"):
        st.session_state.page = "Generate"
        st.rerun()
        
    if st.button("📅 Calendar\n\nSee what you wore on previous days"):
        st.session_state.page = "Calendar"
        st.rerun()

# ----------------- صفحة التصوير (Shoot Station) -----------------
elif st.session_state.page == "Shoot":
    if st.button("⬅️ Back to Home"):
        st.session_state.page = "Home"
        st.rerun()
        
    st.title("📸 Shoot Station")
    st.write("Take a photo or upload an image to add it to your closet.")
    
    image_to_use = st.camera_input("Take a photo")
    if not image_to_use:
        image_to_use = st.file_uploader("Or upload an image", type=["jpg", "png"])
        
    if image_to_use is not None:
        st.image(image_to_use, caption="Preview", width=250)
        with st.form("add_item_form"):
            cat = st.selectbox("Category", database.CATEGORIES)
            color = st.text_input("Color (e.g., Black, Blue)")
            name = st.text_input("Description (e.g., My blue shirt)")
            submit = st.form_submit_button("Save Item")
            
            if submit and color and name:
                database.add_item(st.session_state.email, image_to_use, cat, color, name)
                st.success(f"✅ {name} added to your closet!")
                st.session_state.page = "Wardrobe" # نوديه مباشرة للخزانة بعد ما يسجل
                st.rerun()

# ----------------- صفحة الخزانة (Wardrobe) -----------------
elif st.session_state.page == "Wardrobe":
    if st.button("⬅️ Back to Home"):
        st.session_state.page = "Home"
        st.rerun()
        
    st.title("👗 My Wardrobe")
    
    closet_df = database.get_closet(st.session_state.email)
    
    if closet_df.empty:
        st.info("Your closet is empty. Go to the Shoot Station to add clothes!")
    else:
        category_filter = st.selectbox("Filter by Category", ["ALL"] + database.CATEGORIES)
        if category_filter != "ALL":
            closet_df = closet_df[closet_df['category'] == category_filter]
            
        if closet_df.empty:
            st.warning("No items found in this category.")
        else:
            cols = st.columns(3)
            for index, row in closet_df.iterrows():
                with cols[index % 3]:
                    st.image(row['image_path'], use_container_width=True)
                    st.caption(f"**{row['name']}**\n{row['category']} | {row['color']}")

# ----------------- صفحة توليد اللبسة (AI Stylist) -----------------
elif st.session_state.page == "Generate":
    if st.button("⬅️ Back to Home"):
        st.session_state.page = "Home"
        st.rerun()
        
    st.title("🌤️ AI Stylist")
    
    col_w, col_t = st.columns(2)
    with col_w:
        weather = st.selectbox("Weather", ["Sunny", "Cloudy", "Rainy", "Windy"])
    with col_t:
        temp = st.slider("Temperature (°C)", min_value=-5, max_value=45, value=20)
        
    if st.button("✨ Generate My Outfit"):
        with st.spinner("Styling..."):
            result = recommender.get_outfit_recommendation(st.session_state.email, weather, temp)
            
            if "error" in result:
                st.error(result["error"])
            else:
                for msg in result["messages"]:
                    st.warning(msg)
                
                st.subheader(f"Outfit for {weather}, {temp}°C")
                outfit = result["outfit"]
                
                col1, col2 = st.columns(2)
                with col1:
                    if outfit.get("TOP"):
                        st.image(outfit["TOP"]["image_path"], use_container_width=True)
                        st.caption(f"**Top:** {outfit['TOP']['name']}")
                        if outfit["TOP"]["warning"]: st.warning(outfit["TOP"]["warning"])
                    if outfit.get("OUTER"):
                        st.image(outfit["OUTER"]["image_path"], use_container_width=True)
                        st.caption(f"**Outer:** {outfit['OUTER']['name']}")
                with col2:
                    if outfit.get("BOTTOM"):
                        st.image(outfit["BOTTOM"]["image_path"], use_container_width=True)
                        st.caption(f"**Bottom:** {outfit['BOTTOM']['name']}")
                        if outfit["BOTTOM"]["warning"]: st.warning(outfit["BOTTOM"]["warning"])
                
                st.divider()
                col3, col4 = st.columns(2)
                with col3:
                    if outfit.get("HIJAB"):
                        st.image(outfit["HIJAB"]["image_path"], use_container_width=True)
                        st.caption(f"**Hijab:** {outfit['HIJAB']['name']}")
                with col4:
                    if outfit.get("FOOTWEAR"):
                        st.image(outfit["FOOTWEAR"]["image_path"], use_container_width=True)
                        st.caption(f"**Footwear:** {outfit['FOOTWEAR']['name']}")
                
                st.divider()
                if st.button("👗 Wear This Today"):
                    database.save_outfit_to_calendar(
                        st.session_state.email, weather, temp,
                        outfit["TOP"]["item_id"] if outfit.get("TOP") else None,
                        outfit["BOTTOM"]["item_id"] if outfit.get("BOTTOM") else None,
                        outfit["OUTER"]["item_id"] if outfit.get("OUTER") else None,
                        outfit["FOOTWEAR"]["item_id"] if outfit.get("FOOTWEAR") else None,
                        outfit["HIJAB"]["item_id"] if outfit.get("HIJAB") else None
                    )
                    st.success("✅ Outfit saved to your calendar!")

# ----------------- صفحة التقويم (Calendar) -----------------
elif st.session_state.page == "Calendar":
    if st.button("⬅️ Back to Home"):
        st.session_state.page = "Home"
        st.rerun()
        
    st.title("📅 Outfit History")
    
    _, history_csv = database.get_user_files(st.session_state.email)
    history_df = pd.read_csv(history_csv)
    
    if history_df.empty:
        st.info("No outfits tracked yet. Generate an outfit and save it!")
    else:
        history_df = history_df.sort_values(by="date", ascending=False)
        for index, row in history_df.iterrows():
            with st.expander(f"📅 {row['date']} - {row['weather']} ({row['temperature']}°C)"):
                cols = st.columns(3)
                items_to_show = [
                    ("TOP", row['top_id']), ("BOTTOM", row['bottom_id']), 
                    ("OUTER", row['outer_id']), ("FOOTWEAR", row['footwear_id']),
                    ("HIJAB", row['hijab_id'])
                ]
                
                col_idx = 0
                for cat_name, item_id in items_to_show:
                    if pd.notna(item_id) and item_id != "":
                        item = database.get_item_by_id(st.session_state.email, item_id)
                        if item:
                            with cols[col_idx % 3]:
                                st.image(item['image_path'], use_container_width=True)
                                st.caption(item['name'])
                            col_idx += 1