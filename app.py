"""
======================================================================
 app.py - The main application file for the ShopSphere E-Commerce App
======================================================================

WHAT IS INSIDE THIS FILE
-----------------------
  Section 1  App setup
  Section 2  Logging setup
  Section 3  Database helper functions      <- how we talk to MySQL
  Section 4  Security helpers             <- CSRF, login checks, validation
  Section 5  Public pages                 <- home, products, product details
  Section 6  Authentication              <- register, login, logout
  Section 7  Shopping cart                <- add, update, remove
  Section 8  Checkout and orders          <- place order, order history
  Section 9  Admin panel                  <- manage products / users / orders
  Section 10 Error handlers               <- 404, 403, 500, 503
  Section 11 Run the app                  <- app.run(...)

WHY EVERYTHING IS IN ONE FILE?
------------------------------
This is a learning project, so it is much easier to follow when all the
routes sit together. In a real company you would split this into
"blueprints" - one file per feature (auth.py, cart.py, admin.py ...).
"""

import logging
import os
import re
import secrets
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from mysql.connector import Error as MySQLError, connect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from config import config


# ======================================================================
#  SECTION 1  -  APP SETUP
# ======================================================================

app = Flask(__name__)

# Load every setting from config.py into Flask.
# from_mapping() is the right method for a dictionary.
# (from_object() only works with a class/import path, not a dict.)
app.config.from_mapping(config)

# ---------------------------------------------------------------------
#  BEHIND A REVERSE PROXY (Render, Railway, Nginx, Heroku)
# ---------------------------------------------------------------------
# On a real host the browser talks HTTPS to the proxy, and the proxy
# talks plain HTTP to this app. Without ProxyFix Flask would believe it
# is on http://, build wrong URLs and refuse to set a secure cookie -
# so logins would silently break in production.
#
# We only switch it on when debug is OFF, which is exactly when the app
# is running somewhere else. Local development is untouched.
if not app.config["DEBUG"]:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


# ======================================================================
#  SECTION 2  -  LOGGING
#  Anything written with logger.error() is saved in logs/error.log.
#  This is how we find out what went wrong without breaking the website.
# ======================================================================

LOG_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_FOLDER, "error.log"),
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ======================================================================
#  SECTION 3  -  DATABASE HELPERS
# ----------------------------------------------------------------------
# Every SQL query in this project goes through one of these three
# functions. That keeps the SQL in one place and, more importantly,
# makes sure we ALWAYS use parameterised queries.
#
#  SQL INJECTION = what a parameterised query prevents.
#  Instead of building SQL by gluing strings together:
#      cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
#  ...which lets an attacker type  ' OR '1'='1  and log in as anybody,
#  we pass the value separately:
#      cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
#  MySQL treats the value as plain data, never as part of the query.
# ======================================================================


def get_db():
    """Open one database connection per request and reuse it."""
    if "db" not in g:
        try:
            g.db = connect(
                host=app.config["DB_HOST"],
                port=app.config["DB_PORT"],
                user=app.config["DB_USER"],
                password=app.config["DB_PASSWORD"],
                database=app.config["DB_NAME"],
            )
            # We decide ourselves when to save (commit), so MySQL waits.
            g.db.autocommit = False
        except MySQLError as error:
            logger.error("Database connection failed: %s", error)
            abort(
                503,
                description="We could not reach the database. "
                            "Is MySQL running and is the .env file correct?",
            )
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """Close the connection when the request finishes."""
    connection = g.pop("db", None)
    if connection is not None and connection.is_connected():
        if exception is None:
            try:
                connection.commit()
            except MySQLError as error:
                logger.error("Auto-commit failed: %s", error)
                connection.rollback()
        else:
            connection.rollback()
        connection.close()


def query_all(sql, params=None):
    """Run a SELECT and return every row as a list of dictionaries."""
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(sql, params or ())
    rows = cursor.fetchall()
    cursor.close()
    return rows


def query_one(sql, params=None):
    """Run a SELECT and return the FIRST row, or None if there is none."""
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(sql, params or ())
    row = cursor.fetchone()
    cursor.close()
    return row


def execute(sql, params=None):
    """
    Run an INSERT / UPDATE / DELETE.
    Returns (last_inserted_id_or_None, number_of_rows_changed).
    """
    cursor = get_db().cursor()
    cursor.execute(sql, params or ())
    result = (cursor.lastrowid, cursor.rowcount)
    cursor.close()
    return result


# ======================================================================
#  SECTION 4  -  SECURITY HELPERS
# ======================================================================


# ---- 4.1  CSRF protection -------------------------------------------
# A CSRF token is a random string put in every form. When the form is
# posted back, Flask checks the token still matches the one in the
# session. Without it, any other website could submit forms to ours on
# behalf of a logged in user.

def generate_csrf_token():
    """Return the CSRF token for this session, creating one if needed."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


@app.before_request
def protect_from_csrf():
    """Check the CSRF token on every form submission (POST/PUT/DELETE)."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        token_in_form = request.form.get("csrf_token", "")
        token_in_session = session.get("_csrf_token", "")

        if not token_in_session or token_in_form != token_in_session:
            logger.warning("CSRF check failed for %s", request.path)
            abort(400, description="Your form session expired. Please try again.")


# ---- 4.2  Who is logged in? -----------------------------------------

def get_current_user():
    """Return the logged in user row (as a dict), or None."""
    if "current_user" not in g:
        user_id = session.get("user_id")
        if user_id:
            g.current_user = query_one(
                """SELECT id, name, email, phone, address, is_admin
                   FROM users WHERE id = %s""",
                (user_id,),
            )
            if g.current_user is None:
                # The account was deleted while the cookie still existed.
                session.clear()
                g.current_user = None
        else:
            g.current_user = None
    return g.current_user


def is_admin():
    """True only when a logged in user has is_admin = 1."""
    user = get_current_user()
    return bool(user and user["is_admin"] == 1)


def login_required(view):
    """Block a page from people who are not logged in."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Block a page from anybody who is not an admin."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            flash("Please log in to access the admin panel.", "warning")
            return redirect(url_for("login", next=request.path))
        if not is_admin():
            logger.warning(
                "User %s tried to open the admin panel.", session.get("user_id")
            )
            abort(403)
        return view(*args, **kwargs)

    return wrapped


# ---- 4.3  Small validation helpers -----------------------------------

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PINCODE_PATTERN = re.compile(r"^[0-9]{6}$")
PHONE_PATTERN = re.compile(r"^[0-9]{10}$")


def is_valid_email(email):
    """Basic email shape check (server side, never rely only on HTML)."""
    return bool(EMAIL_PATTERN.match(email or ""))


def password_problem(password):
    """
    Return an error message if the password is weak, otherwise ''.
    Kept simple on purpose: at least 6 characters, letters + numbers.
    """
    if not password or len(password) < 6:
        return "Password must be at least 6 characters long."
    if len(password) > 72:
        return "Password is too long (maximum 72 characters)."
    if not any(char.isalpha() for char in password):
        return "Password must contain at least one letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one number."
    return ""


def clean(text, max_length=None):
    """Trim spaces and (optionally) cut a string to a safe length."""
    result = (text or "").strip()
    if max_length:
        result = result[:max_length]
    return result


def to_int(value, default=None):
    """
    Safely turn user input into a whole number.
    Returns default when the value is not a valid integer.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def to_money(value):
    """
    Turn user input into a valid Decimal (money value).
    Returns None when the input is not a valid amount.
    """
    try:
        amount = Decimal(str(value).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if amount < 0 or amount > Decimal("99999999.99"):
        return None
    return amount


def slugify(text):
    """
    Turn a product name into a URL friendly slug.
        "Nova X1 Smartphone"  ->  "nova-x1-smartphone"
    """
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text) or "item"


def make_unique_slug(text, table="products", ignore_id=None):
    """Add -2, -3, -4 ... until the slug is not already used."""
    base = slugify(text)
    candidate = base
    counter = 2
    while True:
        if ignore_id:
            row = query_one(
                f"SELECT id FROM {table} WHERE slug = %s AND id <> %s",
                (candidate, ignore_id),
            )
        else:
            row = query_one(f"SELECT id FROM {table} WHERE slug = %s", (candidate,))
        if row is None:
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1


def generate_order_code():
    """Make a short, human friendly, unique order id like ORD-260106-4F7A."""
    while True:
        code = f"ORD-{datetime.now():%y%m%d}-{secrets.token_hex(2).upper()}"
        exists = query_one("SELECT id FROM orders WHERE order_code = %s", (code,))
        if exists is None:
            return code


def save_product_image(file_storage):
    """
    Save an uploaded product image inside static/images/uploads.
    Returns the file name, or None when nothing was uploaded.
    Empty strings are returned if the file type is not allowed.
    """
    if not file_storage or not file_storage.filename:
        return None

    # Only allow real image extensions.
    extension = file_storage.filename.rsplit(".", 1)[-1].lower()
    if extension not in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return ""

    # Give the file a random name so two uploads never clash.
    safe_name = f"{secrets.token_hex(8)}.{extension}"
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))
    return safe_name


# ---- 4.4  Small helpers used inside the HTML templates ---------------

@app.template_filter("money")
def money_filter(value):
    """Format a number as money, e.g. 18999.0 -> â‚¹18,999.00"""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    return f"{app.config['CURRENCY']}{amount:,.2f}"


def product_image_url(image_name):
    """Build the URL for a product image (with a fallback placeholder)."""
    if not image_name:
        return url_for("static", filename="images/placeholder.svg")
    if str(image_name).startswith(("http://", "https://", "/")):
        return image_name
    return url_for("static", filename=f"images/{image_name}")


def order_status_colour(status):
    """Map an order status to a CSS class for the coloured badge."""
    return {
        "Pending": "badge-pending",
        "Paid": "badge-paid",
        "Packed": "badge-packed",
        "Shipped": "badge-shipped",
        "Delivered": "badge-delivered",
        "Cancelled": "badge-cancelled",
    }.get(status, "badge-pending")


def demo_rating(product):
    """
    Return a stable demo star rating (4.0 - 4.9) plus a review count.

    PLEASE READ THIS BEFORE THE INTERVIEW
    --------------------------------------
    There is no reviews table in this project, so this is PLACEHOLDER
    DATA - not real customer scores. It is derived from the product id,
    so a product always shows the same stars and nothing flickers when
    you refresh.

    If you ever add real reviews, replace this one function with a
    query and a real AVG(rating). Nothing else needs to change.
    """
    seed = int(product.get("id") or 0)
    stars = round(4.0 + ((seed * 7) % 10) / 10.0, 1)
    reviews = 12 + (seed * 13) % 240
    return stars, reviews


def short_description(text, length=88):
    """Trim a description down so it fits neatly on a product card."""
    text = " ".join((text or "").split())
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "..."


def get_cart_count():
    """Total number of items in the logged in user's cart (for the badge)."""
    user = get_current_user()
    if not user:
        return 0
    row = query_one(
        "SELECT COALESCE(SUM(quantity), 0) AS total FROM cart_items WHERE user_id = %s",
        (user["id"],),
    )
    return int(row["total"]) if row else 0


def get_nav_categories():
    """
    The category list shown in the navbar and the footer.

    It runs on every page, so a database problem must never take the
    whole site down - on failure we just return an empty list.
    """
    try:
        return query_all(
            """SELECT c.id, c.name, c.slug, COUNT(p.id) AS product_count
               FROM categories c
               LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
               GROUP BY c.id
               ORDER BY c.name"""
        )
    except MySQLError as error:
        logger.error("Could not load nav categories: %s", error)
        return []


@app.context_processor
def inject_globals():
    """Make these variables available inside every template."""
    return {
        "current_user": get_current_user(),
        "cart_count": get_cart_count(),
        "nav_categories": get_nav_categories(),
        "site_name": app.config["SITE_NAME"],
        "site_tagline": app.config["SITE_TAGLINE"],
        "csrf_token": generate_csrf_token,
        "money": money_filter,
        "product_image_url": product_image_url,
        "order_status_colour": order_status_colour,
        "demo_rating": demo_rating,
        "short_description": short_description,
        "current_year": datetime.now().year,
    }


# ======================================================================
#  SECTION 5  -  PUBLIC PAGES
# ======================================================================


@app.route("/")
def index():
    """Home page: hero, categories and featured products."""
    categories = query_all(
        """SELECT c.*, COUNT(p.id) AS product_count
           FROM categories c
           LEFT JOIN products p
                  ON p.category_id = c.id AND p.is_active = 1
           GROUP BY c.id
           ORDER BY c.name"""
    )

    featured = query_all(
        """SELECT p.*, c.name AS category_name, c.slug AS category_slug
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE p.is_active = 1 AND p.is_featured = 1
           ORDER BY p.created_at DESC
           LIMIT 8"""
    )

    newest = query_all(
        """SELECT p.*, c.name AS category_name, c.slug AS category_slug
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE p.is_active = 1
           ORDER BY p.created_at DESC, p.id DESC
           LIMIT 4"""
    )

    # ---- "Limited Time Offers" strip -----------------------------
    # The slugs and the discounts live in config.py, so you can change
    # the offers without touching any database table.
    offers = []
    for slug in app.config["OFFER_SLUGS"]:
        row = query_one(
            """SELECT p.*, c.name AS category_name, c.slug AS category_slug
               FROM products p
               LEFT JOIN categories c ON c.id = p.category_id
               WHERE p.slug = %s AND p.is_active = 1""",
            (slug,),
        )
        if row is None:
            continue
        percent = app.config["OFFER_DISCOUNTS"].get(slug, 20)
        current = Decimal(str(row["price"]))
        # Work backwards to show a believable "was" price.
        row["discount_percent"] = percent
        row["was_price"] = (
            current / (Decimal("1") - Decimal(percent) / 100)
        ).quantize(Decimal("0.01"))
        offers.append(row)

    return render_template(
        "index.html",
        page_title="Home",
        categories=categories,
        featured=featured,
        newest=newest,
        offers=offers,
    )


@app.route("/about")
def about():
    """A simple static 'About us' page."""
    stats = query_one(
        """SELECT
             (SELECT COUNT(*) FROM products WHERE is_active = 1)  AS products,
             (SELECT COUNT(*) FROM categories)                   AS categories,
             (SELECT COUNT(*) FROM users    WHERE is_admin = 0) AS customers,
             (SELECT COUNT(*) FROM orders)                       AS orders"""
    )
    return render_template("about.html", page_title="About Us", stats=stats)


@app.route("/contact")
def contact():
    """A simple static 'Contact us' page. The form is a demo only."""
    return render_template("contact.html", page_title="Contact Us")


@app.route("/products")
def products():
    """
    Product listing page with:
      - keyword search  (?q=laptop)
      - category filter (?category=audio)
      - price filter   (?min_price=100&max_price=5000)
      - sorting        (?sort=newest)
      - pagination     (?page=2)
    """
    search_text = clean(request.args.get("q"), 100)
    category_slug = clean(request.args.get("category"), 120)
    sort_option = clean(request.args.get("sort"), 20) or "newest"

    # Only these four columns can ever be used in ORDER BY, so the sort
    # value from the URL can never be used to inject SQL.
    sort_sql = {
        "newest": "p.created_at DESC, p.id DESC",
        "price_low": "p.price ASC",
        "price_high": "p.price DESC",
        "name": "p.name ASC",
    }.get(sort_option, "p.created_at DESC, p.id DESC")

    # Build the WHERE part of the query step by step.
    conditions = ["p.is_active = 1"]
    params = []

    if search_text:
        conditions.append("(p.name LIKE %s OR p.description LIKE %s)")
        keyword = f"%{search_text}%"
        params.extend([keyword, keyword])

    if category_slug:
        conditions.append("c.slug = %s")
        params.append(category_slug)

    min_price = to_money(request.args.get("min_price"))
    max_price = to_money(request.args.get("max_price"))
    if min_price is not None:
        conditions.append("p.price >= %s")
        params.append(min_price)
    if max_price is not None:
        conditions.append("p.price <= %s")
        params.append(max_price)

    where_sql = " AND ".join(conditions)

    # ---- Pagination -------------------------------------------------
    per_page = app.config["ITEMS_PER_PAGE"]
    page_number = max(to_int(request.args.get("page"), 1) or 1, 1)

    count_row = query_one(
        f"""SELECT COUNT(*) AS total
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE {where_sql}""",
        tuple(params),
    )
    total_items = count_row["total"] if count_row else 0
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page_number = min(page_number, total_pages)
    offset = (page_number - 1) * per_page

    product_rows = query_all(
        f"""SELECT p.*, c.name AS category_name, c.slug AS category_slug
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE {where_sql}
            ORDER BY {sort_sql}
            LIMIT %s OFFSET %s""",
        tuple(params) + (per_page, offset),
    )

    all_categories = query_all(
        """SELECT c.*, COUNT(p.id) AS product_count
           FROM categories c
           LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
           GROUP BY c.id
           ORDER BY c.name"""
    )

    return render_template(
        "products.html",
        page_title="Shop",
        products=product_rows,
        categories=all_categories,
        search_text=search_text,
        active_category=category_slug,
        sort_option=sort_option,
        min_price=request.args.get("min_price", ""),
        max_price=request.args.get("max_price", ""),
        page=page_number,
        total_pages=total_pages,
        total_items=total_items,
    )


@app.route("/product/<slug>")
def product_details(slug):
    """Full information about one product, plus a few related products."""
    product = query_one(
        """SELECT p.*, c.name AS category_name, c.slug AS category_slug
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE p.slug = %s AND p.is_active = 1""",
        (slug,),
    )

    # Product not found -> friendly 404 page (not a blank screen).
    if product is None:
        abort(404, description="That product does not exist or is no longer available.")

    related = query_all(
        """SELECT p.*, c.name AS category_name, c.slug AS category_slug
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE p.category_id = %s AND p.id <> %s AND p.is_active = 1
           ORDER BY p.created_at DESC
           LIMIT 4""",
        (product["category_id"], product["id"]),
    )

    return render_template(
        "product_details.html",
        page_title=product["name"],
        product=product,
        related=related,
    )


@app.route("/api/cart-count")
def api_cart_count():
    """Tiny JSON endpoint used by JavaScript to refresh the cart badge."""
    if not get_current_user():
        return jsonify({"count": 0})
    row = query_one(
        """SELECT COALESCE(SUM(quantity), 0) AS total
           FROM cart_items WHERE user_id = %s""",
        (session["user_id"],),
    )
    return jsonify({"count": int(row["total"]) if row else 0})


# ======================================================================
#  SECTION 6  -  AUTHENTICATION
# ======================================================================


@app.route("/register", methods=["GET", "POST"])
def register():
    """Create a new customer account."""
    if get_current_user():
        return redirect(url_for("index"))

    # Values kept in a dict so the form can be re-filled after an error.
    form_data = {"name": "", "email": "", "phone": ""}

    if request.method == "POST":
        form_data["name"] = clean(request.form.get("name"), 100)
        form_data["email"] = clean(request.form.get("email"), 150).lower()
        form_data["phone"] = clean(request.form.get("phone"), 20)
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        errors = []

        # --- Server side validation ---
        if len(form_data["name"]) < 2:
            errors.append("Please enter your full name (at least 2 characters).")

        if not is_valid_email(form_data["email"]):
            errors.append("Please enter a valid email address.")

        if form_data["phone"] and not PHONE_PATTERN.match(form_data["phone"]):
            errors.append("Phone number must be exactly 10 digits.")

        password_error = password_problem(password)
        if password_error:
            errors.append(password_error)

        if password != confirm:
            errors.append("The two passwords do not match.")

        # --- Duplicate email check ---
        if not errors:
            existing = query_one(
                "SELECT id FROM users WHERE email = %s", (form_data["email"],)
            )
            if existing:
                errors.append("An account with this email already exists.")

        # --- Create the account ---
        if not errors:
            try:
                execute(
                    """INSERT INTO users (name, email, password, phone, address, is_admin)
                       VALUES (%s, %s, %s, %s, %s, 0)""",
                    (
                        form_data["name"],
                        form_data["email"],
                        generate_password_hash(password),   # hashed, not plain
                        form_data["phone"] or None,
                        clean(request.form.get("address"), 500) or None,
                    ),
                )
                logger.info("New user registered: %s", form_data["email"])
                flash("Account created! Please log in.", "success")
                return redirect(url_for("login"))
            except MySQLError as error:
                logger.error("Registration failed for %s: %s", form_data["email"], error)
                flash("Could not create your account right now. Please try again.", "error")

        for message in errors:
            flash(message, "error")

    return render_template("register.html", page_title="Create account", form=form_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log a user in. ?next=/cart sends them on after logging in."""
    if get_current_user():
        return redirect(url_for("index"))

    next_page = safe_next_url(request.args.get("next"))
    email_value = ""

    if request.method == "POST":
        email_value = clean(request.form.get("email"), 150).lower()
        password = request.form.get("password", "")
        next_page = safe_next_url(request.form.get("next"))

        if not email_value or not password:
            flash("Please enter both your email and password.", "error")
        else:
            user = query_one(
                "SELECT id, name, email, password, is_admin FROM users WHERE email = %s",
                (email_value,),
            )

            # We give the SAME message for a wrong email and a wrong
            # password on purpose. Otherwise an attacker could use the
            # login form to find out which email addresses exist.
            if user is None or not check_password_hash(user["password"], password):
                logger.info("Failed login attempt for: %s", email_value)
                flash("Incorrect email or password.", "error")
            else:
                session.clear()                 # start a brand new session
                session["user_id"] = user["id"] # remember WHO is logged in
                session.permanent = False
                logger.info("User %s logged in.", email_value)
                flash(f"Welcome back, {user['name']}!", "success")

                if next_page:
                    return redirect(next_page)
                if user["is_admin"] == 1:
                    return redirect(url_for("admin_dashboard"))
                return redirect(url_for("index"))

    return render_template(
        "login.html", page_title="Log in", form_email=email_value, next_page=next_page
    )


@app.route("/logout")
def logout():
    """Clear the session and return to the home page."""
    if get_current_user():
        session.clear()
        flash("You have been logged out.", "info")
    return redirect(url_for("index"))


def safe_next_url(value):
    """
    Only allow redirects to our own pages.
    Without this check an attacker could send
    /login?next=http://evil-site.com and use our login page as a fake.
    """
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return None


# ======================================================================
#  SECTION 7  -  SHOPPING CART
# ======================================================================


@app.route("/cart")
@login_required
def cart():
    """Show the cart, the subtotal and the total."""
    items = get_cart_items()

    if not items:
        # Empty cart is a normal situation, not an error.
        return render_template(
            "cart.html",
            page_title="My Cart",
            items=items,
            subtotal=Decimal("0.00"),
            shipping=Decimal("0.00"),
            total=Decimal("0.00"),
            free_shipping_limit=FREE_SHIPPING_LIMIT,
        )

    subtotal = sum((item["line_total"] for item in items), Decimal("0.00"))
    shipping = shipping_cost(subtotal)
    total = subtotal + shipping

    return render_template(
        "cart.html",
        page_title="My Cart",
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
        free_shipping_limit=FREE_SHIPPING_LIMIT,
    )


@app.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    """Add one product to the cart (or increase its quantity)."""
    product_id = to_int(request.form.get("product_id"))
    quantity = to_int(request.form.get("quantity"), 1)

    if product_id is None:
        flash("Invalid product selected.", "error")
        return redirect(request.referrer or url_for("products"))

    if quantity is None or quantity < 1:
        flash("Quantity must be at least 1.", "error")
        return redirect(request.referrer or url_for("products"))

    product = query_one(
        "SELECT id, name, stock, is_active FROM products WHERE id = %s", (product_id,)
    )
    if product is None or product["is_active"] != 1:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    # How many are ALREADY in the cart?
    existing = query_one(
        "SELECT quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
        (session["user_id"], product_id),
    )
    already_in_cart = existing["quantity"] if existing else 0
    wanted = already_in_cart + quantity

    # STOCK CHECK - never let the cart hold more than we have.
    if wanted > product["stock"]:
        if product["stock"] == 0:
            flash(f"'{product['name']}' is out of stock.", "error")
        else:
            flash(
                f"Only {product['stock']} left in stock. "
                f"Your cart already has {already_in_cart}.",
                "warning",
            )
        return redirect(request.referrer or url_for("product_details",
                                                     slug=query_one(
                                                         "SELECT slug FROM products WHERE id=%s",
                                                         (product_id,))["slug"]))

    if existing:
        execute(
            """UPDATE cart_items SET quantity = %s
               WHERE user_id = %s AND product_id = %s""",
            (wanted, session["user_id"], product_id),
        )
        flash(f"Updated quantity of '{product['name']}' in your cart.", "info")
    else:
        execute(
            """INSERT INTO cart_items (user_id, product_id, quantity)
               VALUES (%s, %s, %s)""",
            (session["user_id"], product_id, quantity),
        )
        flash(f"'{product['name']}' added to your cart.", "success")

    # "Buy now" jumps straight to the checkout page.
    if request.form.get("buy_now"):
        return redirect(url_for("checkout"))

    return redirect(request.referrer or url_for("cart"))


@app.route("/cart/update", methods=["POST"])
@login_required
def cart_update():
    """Change the quantity of a line in the cart (or delete it with 0)."""
    item_id = to_int(request.form.get("item_id"))
    quantity = to_int(request.form.get("quantity"))

    if item_id is None or quantity is None:
        flash("Invalid cart update.", "error")
        return redirect(url_for("cart"))

    item = query_one(
        """SELECT ci.product_id, p.name, p.stock
           FROM cart_items ci
           JOIN products p ON p.id = ci.product_id
           WHERE ci.id = %s AND ci.user_id = %s""",
        (item_id, session["user_id"]),
    )

    if item is None:
        flash("That cart item no longer exists.", "error")
        return redirect(url_for("cart"))

    # Quantity 0 means "remove this line".
    if quantity == 0:
        execute(
            "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
            (item_id, session["user_id"]),
        )
        flash(f"'{item['name']}' removed from your cart.", "info")
        return redirect(url_for("cart"))

    if quantity < 0:
        flash("Quantity cannot be negative.", "error")
        return redirect(url_for("cart"))

    if quantity > item["stock"]:
        flash(f"Only {item['stock']} left in stock.", "warning")
        return redirect(url_for("cart"))

    execute(
        "UPDATE cart_items SET quantity = %s WHERE id = %s AND user_id = %s",
        (quantity, item_id, session["user_id"]),
    )
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
@login_required
def cart_remove():
    """Remove one product from the cart."""
    item_id = to_int(request.form.get("item_id"))

    row = query_one(
        """SELECT p.name FROM cart_items ci
           JOIN products p ON p.id = ci.product_id
           WHERE ci.id = %s AND ci.user_id = %s""",
        (item_id, session["user_id"]),
    )
    execute(
        "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
        (item_id, session["user_id"]),
    )

    if row:
        flash(f"'{row['name']}' removed from your cart.", "info")
    else:
        flash("Item removed from your cart.", "info")

    return redirect(url_for("cart"))


@app.route("/cart/clear", methods=["POST"])
@login_required
def cart_clear():
    """Empty the whole cart."""
    execute("DELETE FROM cart_items WHERE user_id = %s", (session["user_id"],))
    flash("Your cart is now empty.", "info")
    return redirect(url_for("cart"))


# ---- Cart maths helpers ---------------------------------------------

FREE_SHIPPING_LIMIT = Decimal("999.00")
SHIPPING_FLAT_FEE = Decimal("79.00")


def shipping_cost(subtotal):
    """Free delivery above the limit, otherwise a flat fee."""
    if subtotal <= 0:
        return Decimal("0.00")
    if subtotal >= FREE_SHIPPING_LIMIT:
        return Decimal("0.00")
    return SHIPPING_FLAT_FEE


def get_cart_items():
    """
    Return the cart lines with everything the template needs:
    product details, line total, and whether it is still in stock.
    """
    rows = query_all(
        """SELECT ci.id AS item_id, ci.quantity, ci.product_id,
                  p.name, p.slug, p.price, p.stock, p.image, p.is_active,
                  c.name AS category_name
           FROM cart_items ci
           JOIN products p ON p.id = ci.product_id
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE ci.user_id = %s
           ORDER BY ci.added_at DESC""",
        (session["user_id"],),
    )

    items = []
    for row in rows:
        row = dict(row)
        row["line_total"] = Decimal(str(row["price"])) * row["quantity"]
        # Out of stock means: product removed, hidden, or stock ran out.
        row["is_out_of_stock"] = (
            row["is_active"] != 1 or row["stock"] < row["quantity"]
        )
        items.append(row)
    return items


# ======================================================================
#  SECTION 8  -  CHECKOUT AND ORDERS
# ======================================================================


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """
    Mock (demo) checkout - NO real payment gateway.
    We only collect delivery details and save the order in MySQL.
    """
    items = get_cart_items()

    # ---- Empty cart -------------------------------------------------
    if not items:
        flash("Your cart is empty. Add a product before checking out.", "warning")
        return redirect(url_for("cart"))

    # ---- Something sold out: send them back to fix the cart ---------
    blocked = [item for item in items if item["is_out_of_stock"]]
    if blocked:
        names = ", ".join(item["name"] for item in blocked[:3])
        flash(f"Please update your cart first: {names}.", "error")
        return redirect(url_for("cart"))

    subtotal = sum((item["line_total"] for item in items), Decimal("0.00"))
    shipping = shipping_cost(subtotal)
    total = subtotal + shipping

    user = get_current_user()
    form_data = {
        "customer_name": user["name"] or "",
        "email": user["email"] or "",
        "phone": user["phone"] or "",
        "address": user["address"] or "",
        "city": "",
        "state": "",
        "pincode": "",
        "payment_method": "Cash on Delivery",
    }

    if request.method == "POST":
        for field in form_data:
            form_data[field] = clean(request.form.get(field), 500)

        errors = []

        if len(form_data["customer_name"]) < 2:
            errors.append("Please enter your full name.")
        if not is_valid_email(form_data["email"]):
            errors.append("Please enter a valid email address.")
        if not PHONE_PATTERN.match(form_data["phone"] or ""):
            errors.append("Phone number must be exactly 10 digits.")
        if len(form_data["address"]) < 10:
            errors.append("Please enter your full delivery address.")
        if len(form_data["city"]) < 2:
            errors.append("Please enter your city.")
        if len(form_data["state"]) < 2:
            errors.append("Please enter your state.")
        if not PINCODE_PATTERN.match(form_data["pincode"] or ""):
            errors.append("PIN code must be exactly 6 digits.")
        if form_data["payment_method"] not in PAYMENT_METHODS:
            errors.append("Please choose a valid payment method.")

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "checkout.html",
                page_title="Checkout",
                items=items,
                subtotal=subtotal,
                shipping=shipping,
                total=total,
                form=form_data,
                payment_methods=PAYMENT_METHODS,
                free_shipping_limit=FREE_SHIPPING_LIMIT,
            )

        # ---- Save the order (database transaction) ------------------
        order_id = place_order(form_data, items, total)

        if order_id:
            flash("Order placed successfully!", "success")
            return redirect(url_for("order_confirmation", order_id=order_id))

        flash("We could not place the order. Please try again.", "error")
        return redirect(url_for("cart"))

    return render_template(
        "checkout.html",
        page_title="Checkout",
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
        form=form_data,
        payment_methods=PAYMENT_METHODS,
        free_shipping_limit=FREE_SHIPPING_LIMIT,
    )


PAYMENT_METHODS = ["Cash on Delivery", "UPI (Demo)", "Card (Demo)"]


def place_order(form_data, items, total):
    """
    Save the order, its items, reduce the stock and empty the cart -
    all inside ONE database transaction.

    A transaction means: either everything succeeds, or nothing is
    saved at all. If the server crashes half way we never end up with
    an order that has no items.
    """
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        # Re-check the stock with a row lock so two people buying the
        # last item at the same time cannot both succeed.
        cursor.execute(
            """SELECT p.id, p.name, p.price, p.stock, ci.quantity
               FROM cart_items ci
               JOIN products p ON p.id = ci.product_id
               WHERE ci.user_id = %s
               FOR UPDATE""",
            (session["user_id"],),
        )
        fresh_items = cursor.fetchall()
        if not fresh_items:
            cursor.close()
            return None

        for item in fresh_items:
            if item["stock"] < item["quantity"]:
                cursor.close()
                flash(f"'{item['name']}' just went out of stock.", "error")
                return None

        # 1. The order header
        cursor.execute(
            """INSERT INTO orders
               (order_code, user_id, customer_name, email, phone,
                address, city, state, pincode, payment_method,
                total_amount, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')""",
            (
                generate_order_code(),
                session["user_id"],
                form_data["customer_name"],
                form_data["email"],
                form_data["phone"],
                form_data["address"],
                form_data["city"],
                form_data["state"],
                form_data["pincode"],
                form_data["payment_method"],
                total,
            ),
        )
        order_id = cursor.lastrowid

        # 2. One row per product
        for item in fresh_items:
            cursor.execute(
                """INSERT INTO order_items
                   (order_id, product_id, product_name, price, quantity)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    order_id,
                    item["id"],
                    item["name"],
                    item["price"],   # price copied = invoice stays correct
                    item["quantity"],
                ),
            )
            # 3. Reduce the stock
            cursor.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (item["quantity"], item["id"]),
            )

        # 4. Empty the cart
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session["user_id"],))

        database.commit()      # SAVE everything
        cursor.close()
        logger.info("Order %s placed by user %s", order_id, session["user_id"])
        return order_id

    except MySQLError as error:
        database.rollback()    # UNDO everything
        cursor.close()
        logger.error("Order failed: %s", error)
        return None


@app.route("/order/<int:order_id>/confirmation")
@login_required
def order_confirmation(order_id):
    """'Thank you' page shown right after checkout."""
    order = get_order_for_user(order_id)
    if order is None:
        abort(404, description="Order not found.")

    items = get_order_items(order_id)

    return render_template(
        "order_details.html",
        page_title=f"Order {order['order_code']}",
        order=order,
        items=items,
        is_confirmation=True,
    )


@app.route("/orders")
@login_required
def orders():
    """List of the logged in customer's past orders."""
    order_rows = query_all(
        """SELECT o.*, COUNT(oi.id) AS item_count,
                  COALESCE(SUM(oi.quantity), 0) AS total_items
           FROM orders o
           LEFT JOIN order_items oi ON oi.order_id = o.id
           WHERE o.user_id = %s
           GROUP BY o.id
           ORDER BY o.created_at DESC""",
        (session["user_id"],),
    )
    return render_template(
        "orders.html", page_title="My Orders", orders=order_rows
    )


@app.route("/orders/<int:order_id>")
@login_required
def order_details(order_id):
    """One order with its items."""
    order = get_order_for_user(order_id)
    if order is None:
        abort(404, description="Order not found.")

    return render_template(
        "order_details.html",
        page_title=f"Order {order['order_code']}",
        order=order,
        items=get_order_items(order_id),
        is_confirmation=False,
    )


def get_order_for_user(order_id):
    """
    Fetch an order, but ONLY if it belongs to the logged in customer.
    A customer must never be able to read somebody else's order by
    guessing the id in the URL.
    """
    user = get_current_user()
    if user["is_admin"] == 1:
        return query_one("SELECT * FROM orders WHERE id = %s", (order_id,))
    return query_one(
        "SELECT * FROM orders WHERE id = %s AND user_id = %s",
        (order_id, session["user_id"]),
    )


def get_order_items(order_id):
    return query_all(
        """SELECT oi.*, p.slug, p.image
           FROM order_items oi
           LEFT JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = %s
           ORDER BY oi.id""",
        (order_id,),
    )


# ======================================================================
#  SECTION 9  -  ADMIN PANEL
# ======================================================================


@app.route("/admin")
@admin_required
def admin_dashboard():
    """Numbers + recent activity for the admin."""
    stats = query_one(
        """SELECT
             (SELECT COUNT(*) FROM users   WHERE is_admin = 0) AS customers,
             (SELECT COUNT(*) FROM products)                    AS products,
             (SELECT COUNT(*) FROM orders)                      AS orders,
             (SELECT COUNT(*) FROM orders WHERE status = 'Pending') AS pending_orders,
             (SELECT COALESCE(SUM(total_amount), 0) FROM orders
                WHERE status <> 'Cancelled')                    AS revenue"""
    )

    recent_orders = query_all(
        """SELECT o.*, u.name AS user_name
           FROM orders o
           JOIN users u ON u.id = o.user_id
           ORDER BY o.created_at DESC
           LIMIT 8"""
    )

    low_stock = query_all(
        """SELECT p.*, c.name AS category_name, c.slug AS category_slug
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE p.is_active = 1 AND p.stock <= %s
           ORDER BY p.stock ASC
           LIMIT 8""",
        (app.config["LOW_STOCK_THRESHOLD"],),
    )

    top_products = query_all(
        """SELECT p.name, p.slug, p.price,
                  COALESCE(SUM(oi.quantity), 0) AS sold
           FROM order_items oi
           JOIN products p ON p.id = oi.product_id
           GROUP BY p.id
           ORDER BY sold DESC
           LIMIT 5"""
    )

    return render_template(
        "admin/dashboard.html", page_title="Admin Dashboard", stats=stats,
        recent_orders=recent_orders, low_stock=low_stock, top_products=top_products
    )


# ---------- 9.1  Product management ----------------------------------


@app.route("/admin/products")
@admin_required
def admin_products():
    """Table of every product with edit / delete buttons."""
    search_text = clean(request.args.get("q"), 100)

    if search_text:
        keyword = f"%{search_text}%"
        rows = query_all(
            """SELECT p.*, c.name AS category_name, c.slug AS category_slug
               FROM products p
               LEFT JOIN categories c ON c.id = p.category_id
               WHERE p.name LIKE %s OR p.slug LIKE %s
               ORDER BY p.id DESC""",
            (keyword, keyword),
        )
    else:
        rows = query_all(
            """SELECT p.*, c.name AS category_name, c.slug AS category_slug
               FROM products p
               LEFT JOIN categories c ON c.id = p.category_id
               ORDER BY p.id DESC"""
        )

    return render_template(
        "admin/products.html",
        page_title="Manage Products",
        products=rows,
        search_text=search_text,
    )


def read_product_form():
    """Read and validate the add/edit product form."""
    data = {
        "name": clean(request.form.get("name"), 200),
        "description": clean(request.form.get("description"), 2000),
        "image_current": clean(request.form.get("image_current"), 255),
    }
    data["price"] = to_money(request.form.get("price"))
    data["stock"] = to_int(request.form.get("stock"))
    data["category_id"] = to_int(request.form.get("category_id"))
    data["is_featured"] = 1 if request.form.get("is_featured") else 0
    data["is_active"] = 1 if request.form.get("is_active") else 0

    errors = []
    if len(data["name"]) < 3:
        errors.append("Product name must be at least 3 characters.")
    if data["price"] is None or data["price"] <= 0:
        errors.append("Please enter a valid price greater than 0.")
    if data["stock"] is None or data["stock"] < 0:
        errors.append("Stock must be 0 or a positive number.")
    if len(data["description"]) < 10:
        errors.append("Please write a description of at least 10 characters.")

    # Check the category really exists (prevents a broken foreign key).
    if data["category_id"]:
        if not query_one(
            "SELECT id FROM categories WHERE id = %s", (data["category_id"],)
        ):
            errors.append("Please choose a valid category.")
            data["category_id"] = None

    return data, errors


@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    """Form to create a new product."""
    categories = query_all("SELECT id, name FROM categories ORDER BY name")
    data = {
        "name": "",
        "description": "",
        "price": "",
        "stock": "",
        "category_id": "",
        "image_current": "placeholder.svg",
        "is_featured": 0,
        "is_active": 1,
    }

    if request.method == "POST":
        data, errors = read_product_form()
        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "admin/add_product.html",
                page_title="Add Product",
                categories=categories,
                form=data,
            )

        try:
            image_name = save_product_image(request.files.get("image"))
            if image_name == "":
                flash("Only JPG, PNG, GIF or WEBP images are allowed.", "error")
                return render_template(
                    "admin/add_product.html",
                    page_title="Add Product",
                    categories=categories,
                    form=data,
                )

            new_id, _ = execute(
                """INSERT INTO products
                   (name, slug, description, price, stock, image,
                    category_id, is_featured, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    data["name"],
                    make_unique_slug(data["name"]),
                    data["description"],
                    data["price"],
                    data["stock"],
                    image_name or "placeholder.svg",
                    data["category_id"],
                    data["is_featured"],
                    data["is_active"],
                ),
            )
            logger.info("Product %s created by admin %s", new_id, session["user_id"])
            flash(f"Product '{data['name']}' added successfully.", "success")
            return redirect(url_for("admin_products"))

        except MySQLError as error:
            logger.error("Add product failed: %s", error)
            flash("Could not save the product. Please try again.", "error")

    return render_template(
        "admin/add_product.html",
        page_title="Add Product",
        categories=categories,
        form=data,
    )


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    """Change an existing product."""
    categories = query_all("SELECT id, name FROM categories ORDER BY name")

    product = query_one("SELECT * FROM products WHERE id = %s", (product_id,))
    if product is None:
        abort(404, description="Product not found.")

    if request.method == "POST":
        data, errors = read_product_form()
        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "admin/edit_product.html",
                page_title="Edit Product",
                categories=categories,
                form={**product, **data},
                product_id=product_id,
            )

        try:
            image_name = save_product_image(request.files.get("image"))
            if image_name == "":
                flash("Only JPG, PNG, GIF or WEBP images are allowed.", "error")
                return render_template(
                    "admin/edit_product.html",
                    page_title="Edit Product",
                    categories=categories,
                    form={**product, **data},
                    product_id=product_id,
                )

            final_image = image_name or (data["image_current"] or "placeholder.svg")

            execute(
                """UPDATE products
                   SET name = %s, slug = %s, description = %s, price = %s,
                       stock = %s, image = %s, category_id = %s,
                       is_featured = %s, is_active = %s
                   WHERE id = %s""",
                (
                    data["name"],
                    make_unique_slug(data["name"], ignore_id=product_id),
                    data["description"],
                    data["price"],
                    data["stock"],
                    final_image,
                    data["category_id"],
                    data["is_featured"],
                    data["is_active"],
                    product_id,
                ),
            )
            logger.info("Product %s updated", product_id)
            flash("Product updated successfully.", "success")
            return redirect(url_for("admin_products"))

        except MySQLError as error:
            logger.error("Edit product failed: %s", error)
            flash("Could not update the product. Please try again.", "error")

    return render_template(
        "admin/edit_product.html",
        page_title="Edit Product",
        categories=categories,
        form=product,
        product_id=product_id,
    )


@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    """
    Delete a product.

    We do NOT delete products that were already ordered - old invoices
    must stay correct. Instead we set is_active = 0 which hides the
    product from the shop while keeping the order history intact.
    """
    product = query_one("SELECT name FROM products WHERE id = %s", (product_id,))
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("admin_products"))

    ordered_before = query_one(
        "SELECT id FROM order_items WHERE product_id = %s LIMIT 1", (product_id,)
    )

    if ordered_before:
        execute("UPDATE products SET is_active = 0 WHERE id = %s", (product_id,))
        flash(
            f"'{product['name']}' was ordered before, so it was archived "
            "(hidden from the shop) instead of deleted.",
            "warning",
        )
    else:
        execute("DELETE FROM products WHERE id = %s", (product_id,))
        flash(f"'{product['name']}' deleted.", "success")

    logger.info("Product %s deleted by admin", product_id)
    return redirect(url_for("admin_products"))


# ---------- 9.2  Users and orders ------------------------------------


@app.route("/admin/users")
@admin_required
def admin_users():
    """Every registered user with their order count."""
    rows = query_all(
        """SELECT u.id, u.name, u.email, u.phone, u.is_admin, u.created_at,
                  COUNT(o.id) AS order_count,
                  COALESCE(SUM(o.total_amount), 0) AS spent
           FROM users u
           LEFT JOIN orders o ON o.user_id = u.id
           GROUP BY u.id
           ORDER BY u.created_at DESC"""
    )
    return render_template(
        "admin/users.html", page_title="Users", users=rows
    )


@app.route("/admin/orders")
@admin_required
def admin_orders():
    """Every order, with a filter by status."""
    status = clean(request.args.get("status"), 30)

    if status and status in ORDER_STATUSES:
        rows = query_all(
            """SELECT o.*, u.name AS user_name, u.email AS user_email
               FROM orders o
               JOIN users u ON u.id = o.user_id
               WHERE o.status = %s
               ORDER BY o.created_at DESC""",
            (status,),
        )
    else:
        status = ""
        rows = query_all(
            """SELECT o.*, u.name AS user_name, u.email AS user_email
               FROM orders o
               JOIN users u ON u.id = o.user_id
               ORDER BY o.created_at DESC"""
        )

    return render_template(
        "admin/orders.html",
        page_title="Orders",
        orders=rows,
        active_status=status,
        status_options=ORDER_STATUSES,
    )


@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_details(order_id):
    order = query_one(
        """SELECT o.*, u.name AS user_name, u.email AS user_email
           FROM orders o
           JOIN users u ON u.id = o.user_id
           WHERE o.id = %s""",
        (order_id,),
    )
    if order is None:
        abort(404, description="Order not found.")

    return render_template(
        "admin/order_details.html",
        page_title=f"Order {order['order_code']}",
        order=order,
        items=get_order_items(order_id),
        status_options=ORDER_STATUSES,
    )


@app.route("/admin/orders/update-status", methods=["POST"])
@admin_required
def admin_update_order_status():
    """Change the status of an order (Pending -> Packed -> ...)."""
    order_id = to_int(request.form.get("order_id"))
    new_status = clean(request.form.get("status"), 30)

    if order_id is None:
        flash("Invalid order.", "error")
        return redirect(url_for("admin_orders"))

    if new_status not in ORDER_STATUSES:
        flash("Invalid order status.", "error")
        return redirect(url_for("admin_orders"))

    order = query_one("SELECT order_code, status FROM orders WHERE id = %s", (order_id,))
    if order is None:
        flash("Order not found.", "error")
        return redirect(url_for("admin_orders"))

    if order["status"] == new_status:
        flash("The order already has that status.", "info")
    else:
        execute(
            "UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id)
        )
        flash(
            f"Order {order['order_code']}: {order['status']} -> {new_status}.",
            "success",
        )

    logger.info(
        "Order %s status changed to %s by admin %s",
        order_id, new_status, session["user_id"],
    )
    return redirect(request.referrer or url_for("admin_orders"))


ORDER_STATUSES = ["Pending", "Paid", "Packed", "Shipped", "Delivered", "Cancelled"]


# ======================================================================
#  SECTION 10  -  ERROR HANDERS
#  These render friendly pages instead of Flask's plain error text.
# ======================================================================


@app.errorhandler(400)
def error_400(error):
    return render_template(
        "errors/400.html", page_title="Bad request",
        message=getattr(error, "description", "The request could not be understood."),
    ), 400


@app.errorhandler(403)
def error_403(error):
    return render_template(
        "errors/403.html", page_title="Access denied",
        message="You do not have permission to view this page.",
    ), 403


@app.errorhandler(404)
def error_404(error):
    return render_template(
        "errors/404.html", page_title="Page not found",
        message=getattr(error, "description", "The page you were looking for does not exist."),
    ), 404


@app.errorhandler(500)
def error_500(error):
    logger.error("Unhandled server error: %s", error)
    return render_template(
        "errors/500.html", page_title="Something went wrong",
        message="An unexpected error happened. We have logged it and will look into it.",
    ), 500


@app.errorhandler(503)
def error_503(error):
    return render_template(
        "errors/500.html", page_title="Service unavailable",
        message=getattr(error, "description", "The service is temporarily unavailable."),
    ), 503


@app.errorhandler(MySQLError)
def error_database(error):
    """Any uncaught MySQL error becomes a friendly page, not a crash."""
    logger.error("Database error: %s", error)
    return render_template(
        "errors/500.html", page_title="Database problem",
        message="We had a problem talking to the database. Please try again.",
    ), 500


# ======================================================================
#  SECTION 11  -  RUN THE APP
# ======================================================================

if __name__ == "__main__":
    # Create the uploads folder if it is missing.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # host=0.0.0.0 also lets you open the site from your phone on the
    # same Wi-Fi (use http://<your-pc-ip>:5000 on the phone).
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=app.config["DEBUG"],
    )