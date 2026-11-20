import os
import pandas as pd

base_dir = os.path.dirname(os.path.abspath(__file__))
weather_path = os.path.join(base_dir, "data", "raw", "weather", "weather.csv")

print("Loading weather data...")
weather = pd.read_csv(weather_path)

print("\n--- Columns ---")
print(weather.columns.tolist())

print("\n--- First 3 Rows ---")
print(weather.head(3))

# Let's see the different weather conditions
for col in weather.columns:
    if 'weather' in col.lower():
        print(f"\n--- Unique values in '{col}' ---")
        print(weather[col].value_counts())