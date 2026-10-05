import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DOCS_DIR = BASE_DIR / "documentation"
DATABASE_DIR = BASE_DIR / "database"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Raw Olist CSV paths
RAW_FILES = {
    "customers": RAW_DATA_DIR / "olist_customers_dataset.csv",
    "orders": RAW_DATA_DIR / "olist_orders_dataset.csv",
    "order_items": RAW_DATA_DIR / "olist_order_items_dataset.csv",
    "order_payments": RAW_DATA_DIR / "olist_order_payments_dataset.csv",
    "order_reviews": RAW_DATA_DIR / "olist_order_reviews_dataset.csv",
    "products": RAW_DATA_DIR / "olist_products_dataset.csv",
    "sellers": RAW_DATA_DIR / "olist_sellers_dataset.csv",
    "category_translations": RAW_DATA_DIR / "product_category_name_translation.csv",
    "geolocation": RAW_DATA_DIR / "olist_geolocation_dataset.csv",
}

# Output CSV paths (what we load into MySQL)
PROCESSED_FILES = {
    "customer": PROCESSED_DATA_DIR / "customer.csv",
    "customer_phone": PROCESSED_DATA_DIR / "customer_phone.csv",
    "address": PROCESSED_DATA_DIR / "address.csv",
    "vendor": PROCESSED_DATA_DIR / "vendor.csv",
    "category": PROCESSED_DATA_DIR / "category.csv",
    "warehouse": PROCESSED_DATA_DIR / "warehouse.csv",
    "product": PROCESSED_DATA_DIR / "product.csv",
    "product_tag": PROCESSED_DATA_DIR / "product_tag.csv",
    "inventory": PROCESSED_DATA_DIR / "inventory.csv",
    "orders": PROCESSED_DATA_DIR / "orders.csv",
    "order_item": PROCESSED_DATA_DIR / "order_item.csv",
    "payment": PROCESSED_DATA_DIR / "payment.csv",
}

# MySQL connection settings (read from .env)
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "multivendor_ecommerce_db"),
    "charset": "utf8mb4",
    "autocommit": False,
}

# How many rows to INSERT at a time
BATCH_SIZE = 5000

