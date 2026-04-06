from PIL import Image
import os

png_path = r"C:\Users\eemah\.gemini\antigravity\brain\4369145b-b078-4446-8feb-066f69ee30ec\spectrometer_icon_1775474019624.png"
ico_path = r"c:\Users\eemah\OceanOptics_Project\app_icon.ico"

try:
    img = Image.open(png_path)
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Successfully created {ico_path}")
except Exception as e:
    print(f"Error: {e}")
