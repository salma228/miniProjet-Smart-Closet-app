import os
import pandas as pd

base_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(base_dir, "data", "raw", "weather", "weather.csv")
output_path = os.path.join(base_dir, "data", "processed", "weather_en.csv")

print("Loading raw weather data...")
df = pd.read_csv(input_path)

# 1. Rename the columns to English
column_mapping = {
    'Jenis Kelamin': 'Gender',
    'Kondisi Cuaca': 'Weather',
    'Suhu': 'Temperature',
    'Kelembapan': 'Humidity',
    'Lokasi': 'Location',
    'Aktivitas': 'Activity',
    'Durasi': 'Duration',
    'Atasan': 'Topwear',
    'Bawahan': 'Bottomwear',
    'Pakaian Luar': 'Outerwear',
    'Alas Kaki': 'Footwear'
}
df = df.rename(columns=column_mapping)

# 2. Translate the values inside the columns
weather_map = {'Cerah': 'Sunny', 'Hujan': 'Rainy', 'Mendung': 'Cloudy', 'Berangin': 'Windy'}
gender_map = {'Laki-laki': 'Male', 'Perempuan': 'Female'}

# Translate clothing items to match your Fashion dataset
top_map = {'Kaos': 'Tshirts', 'Kemeja': 'Shirts', 'Blouse': 'Tops', 'Jas': 'Blazers'}
bottom_map = {'Celana Panjang': 'Trousers', 'Celana Pendek': 'Shorts', 'Rok': 'Skirts'}
outer_map = {'Tanpa Pakaian Luar': 'None', 'Jaket': 'Jackets', 'Hoodie': 'Sweatshirts', 'Rompi': 'Jackets'}
footwear_map = {'Sneakers': 'Casual Shoes', 'Sepatu Bot': 'Boots', 'Sandal': 'Sandals', 'Sepatu Pantofel': 'Formal Shoes'}

# Apply translations (if a word isn't in the dictionary, it stays as it was)
df['Weather'] = df['Weather'].map(weather_map).fillna(df['Weather'])
df['Gender'] = df['Gender'].map(gender_map).fillna(df['Gender'])
df['Topwear'] = df['Topwear'].map(top_map).fillna(df['Topwear'])
df['Bottomwear'] = df['Bottomwear'].map(bottom_map).fillna(df['Bottomwear'])
df['Outerwear'] = df['Outerwear'].map(outer_map).fillna(df['Outerwear'])
df['Footwear'] = df['Footwear'].map(footwear_map).fillna(df['Footwear'])

# 3. Save the translated dataset
df.to_csv(output_path, index=False)

print("\n Dataset Processing Complete.")
print("Standardized Weather-Outfit Configuration Preview:\n")
print(df[['Weather', 'Temperature', 'Topwear', 'Bottomwear', 'Outerwear', 'Footwear']].head(10))