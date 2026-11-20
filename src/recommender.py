import os
import pandas as pd
import database

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
weather_csv = os.path.join(base_dir, "data", "processed", "weather_en.csv")

def get_outfit_recommendation(email, weather_input, temp_input):
    if not os.path.exists(weather_csv):
        return {"error": "Weather dataset not found."}
    weather_df = pd.read_csv(weather_csv)

    # جلب خزانة المستخدم الحالي
    closet_df = database.get_closet(email)
    if closet_df.empty:
        return {"error": "Your closet is empty! Please add some clothes first."}

    temp_band = "Hot" if temp_input > 25 else ("Mild" if temp_input >= 15 else "Cold")
    
    subset = weather_df[weather_df['Weather'] == weather_input]
    if temp_band == "Hot":
        subset = subset[subset['Temperature'] > 25]
    elif temp_band == "Cold":
        subset = subset[subset['Temperature'] < 15]
    else:
        subset = subset[(subset['Temperature'] >= 15) & (subset['Temperature'] <= 25)]

    if subset.empty:
        subset = weather_df[weather_df['Weather'] == weather_input]

    rec_outer = subset['Outerwear'].mode().iloc[0] if not subset['Outerwear'].mode().empty else "None"

    required_categories = ["TOP", "BOTTOM", "FOOTWEAR"]
    if rec_outer != "None" or temp_band == "Cold":
        required_categories.append("OUTER")

    # جلب التاريخ الخاص بالمستخدم
    recently_worn_ids = database.get_items_worn_last_3_days(email)

    final_outfit = {}
    missing_categories = []

    for category in required_categories:
        cat_items = closet_df[closet_df['category'] == category]

        if cat_items.empty:
            missing_categories.append(category)
            final_outfit[category] = None
            continue

        if category in ["OUTER", "FOOTWEAR"]:
            chosen_item = cat_items.sample(1).iloc[0].to_dict()
            chosen_item["warning"] = None
        else:
            fresh_items = cat_items[~cat_items['item_id'].isin(recently_worn_ids)]
            recent_items = cat_items[cat_items['item_id'].isin(recently_worn_ids)]

            if not fresh_items.empty:
                chosen_item = fresh_items.sample(1).iloc[0].to_dict()
                chosen_item["warning"] = None
            else:
                chosen_item = recent_items.sample(1).iloc[0].to_dict()
                chosen_item["warning"] = "⚠️ You wore this recently (within 3 days)"

        final_outfit[category] = chosen_item

    hijab_items = closet_df[closet_df['category'] == "HIJAB"]
    if not hijab_items.empty:
        bottom_item = final_outfit.get("BOTTOM")
        if bottom_item:
            bottom_color = str(bottom_item.get("color", "")).lower()
            matched_hijabs = hijab_items[hijab_items['color'] == bottom_color]
            if matched_hijabs.empty:
                neutrals = ['black', 'white', 'beige', 'grey', 'gray', 'navy', 'brown']
                matched_hijabs = hijab_items[hijab_items['color'].isin(neutrals)]
            if matched_hijabs.empty:
                matched_hijabs = hijab_items
        else:
            matched_hijabs = hijab_items

        chosen_hijab = matched_hijabs.sample(1).iloc[0].to_dict()
        chosen_hijab["warning"] = None
        final_outfit["HIJAB"] = chosen_hijab
    else:
        final_outfit["HIJAB"] = None

    response = {
        "weather": weather_input, "temperature": temp_input,
        "outfit": final_outfit, "missing_categories": missing_categories, "messages": []
    }

    for missing in missing_categories:
        response["messages"].append(f"I didn't find a {missing.lower()} in your closet. Do you want to add one or continue without it?")
    
    if "OUTER" in missing_categories and temp_band == "Cold":
        response["messages"].append(f"Friendly reminder: It's {temp_input}°C outside and you have no outerwear. You might feel cold!")

    return response