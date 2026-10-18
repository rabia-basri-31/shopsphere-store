"""
=====================================================================
 config.py - All configuration for the e-commerce app lives here.
=====================================================================

WHY THIS FILE EXISTS
--------------------
We should NEVER hard-code a password or a secret key inside our code.
Instead we keep those values in a hidden file called ".env" and read
them here using environment variables.

Files that work together:
    .env          -> real values (never uploaded to GitHub)
    .env.example  -> sample/template file (safe to upload to GitHub)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# BASE_DIR = absolute path of the folder that contains config.py.
# Using __file__ means the code works no matter where you run it from.
BASE_DIR = Path(__file__).resolve().parent

# Read the .env file and put every KEY=value pair into the environment.
load_dotenv(BASE_DIR / ".env")


class Config:
    """Every setting the application needs, read from environment variables."""

    # ---------------------------------------------------------------
    # Flask settings
    # ---------------------------------------------------------------
    # SECRET_KEY signs the session cookie so it cannot be tampered with.
    # If someone steals this key they could pretend to be any user.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me")

    # DEBUG = True shows the detailed error page while you develop.
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # ---------------------------------------------------------------
    # MySQL database settings
    # ---------------------------------------------------------------
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "ecommerce_db")

    # ---------------------------------------------------------------
    # Website / shop settings
    # ---------------------------------------------------------------
    SITE_NAME = os.getenv("SITE_NAME", "ShopSphere")
    SITE_TAGLINE = os.getenv("SITE_TAGLINE", "Everyday essentials, delivered")
    CURRENCY = os.getenv("CURRENCY", "₹")
    ITEMS_PER_PAGE = 9
    LOW_STOCK_THRESHOLD = 5

    # ---------------------------------------------------------------
    # Product image uploads (used by the admin panel)
    # ---------------------------------------------------------------
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "images" / "uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB maximum file size
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # ---------------------------------------------------------------
    # Demo content for the "Limited Time Offers" strip on the home
    # page. This is deliberately NOT stored in the database, so you can
    # change the offers without touching any table.
    # Key = product slug, value = percentage off.
    # ---------------------------------------------------------------
    OFFER_SLUGS = ["aero-running-shoes", "pulse-wireless-earbuds", "vertex-14-laptop"]
    OFFER_DISCOUNTS = {
        "aero-running-shoes": 30,
        "pulse-wireless-earbuds": 25,
        "vertex-14-laptop": 15,
    }

    # Create the uploads folder automatically so the app never crashes.
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------------
# Turn the class above into a plain dictionary.
# Flask's  app.config.from_object()  expects a dictionary/object,
# and this little trick keeps us from repeating every key by hand.
# (Only UPPERCASE names are settings - the dunder names are skipped.)
# ---------------------------------------------------------------
config = {
    name: value
    for name, value in vars(Config).items()
    if name.isupper()
}