import os

folder_path = r"C:\Users\DELL\OneDrive\Desktop\Fia\miniProjetCloset\data\raw\fashion"

print(f"Looking inside: {folder_path}\n")

if os.path.exists(folder_path):
    print("Here is what Python actually sees in that folder:")
    files = os.listdir(folder_path)
    for f in files:
        print(f" -> '{f}'")
else:
    print("❌ ERROR: The folder itself does not exist. Check for typos in your folder names.")