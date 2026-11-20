import os
import pandas as pd

# This finds the exact folder where explore.py is saved
base_dir = os.path.dirname(os.path.abspath(__file__))

# This creates the full, correct path to the CSV
csv_path = os.path.join(base_dir, "data", "raw", "fashion", "styles.csv")

print(f"Looking for data at: {csv_path}")
fashion = pd.read_csv(csv_path, on_bad_lines="skip")

print("Shape:", fashion.shape)
print("Columns:", fashion.columns.tolist())

print("\n--- Master Categories ---")
print(fashion["masterCategory"].value_counts())

print("\n--- Top 15 Article Types ---")
print(fashion["articleType"].value_counts().head(15))