import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_DATA_PATH = os.path.join(BASE_DIR, "data/raw/retail_store_inventory.csv")

PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data/processed/processed_sales_data.csv")
