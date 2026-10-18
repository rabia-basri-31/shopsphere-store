"""
======================================================================
 tests/smoke_test.py  -  Automatic end-to-end check of the whole shop
======================================================================

WHAT THIS DOES
    Walks through every feature the way a customer and an admin would,
    and checks that the site behaves correctly at each step. It uses
    Flask's built-in test client, so it starts no server and needs no
    browser.

WHY IT EXISTS
    Before showing a project to an employer, you want proof that every
    button works. Run this after any change.

HOW TO RUN
    python tests/smoke_test.py

    That is all. The script creates its own throwaway accounts, runs
    every check, then deletes them again - so it needs nothing from you
    and leaves your database as it found it.
======================================================================
"""

import os
import re
import sys
import time

# Make sure the project root is importable, so `from app import app`
# works no matter which folder you run this file from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

# -------------------------------------------------------------------------
# The accounts this run will create and then delete again.
# The email addresses are made unique per run, so two runs never collide.
# -------------------------------------------------------------------------
RUN_ID = str(int(time.time()))[::-1]
ADMIN_EMAIL = f"smoke-admin-{RUN_ID}@example.test"
ADMIN_PASSWORD = "SmokeAdmin123"
CUSTOMER_EMAIL = f"smoke-user-{RUN_ID}@example.test"
CUSTOMER_PASSWORD = "SmokeUser123"
OTHER_EMAIL = f"smoke-other-{RUN_ID}@example.test"
OTHER_PASSWORD = "SmokeOther123"

# The name used for the product the admin tests create, so that cleanup
# can find and remove exactly that product and nothing else.
TEST_PRODUCT = "Smoke Test Widget"

# -------------------------------------------------------------------------
# Test helpers
# -------------------------------------------------------------------------
TOKEN_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
NAME_RE = re.compile(r'name="customer_name" value="([^"]*)"')

passed, failed = [], []


def check(name, condition, extra=""):
    """Record one pass/fail result and print it."""
    if condition:
        passed.append(name)
        print(f"  PASS   {name}")
    else:
        failed.append(name)
        print(f"  FAIL   {name}   {extra}")


def token_of(response):
    """Pull the hidden CSRF token out of a rendered page."""
    match = TOKEN_RE.search(response.get_data(as_text=True))
    return match.group(1) if match else None


def main():
    app.config["TESTING"] = True

    run_id = str(int(time.time()))[::-1]

    # --- Clean up leftovers from a previous run -------------------------
    with app.app_context():
        from app import execute, query_all
        execute("DELETE FROM cart_items")
        execute("DELETE FROM products WHERE name LIKE %s", (f"{TEST_PRODUCT}%",))

        # --- Create the three throwaway accounts this run needs -------
        # One admin (is_admin = 1) and two customers, so the
        # "can another customer see my order?" check has something to
        # compare against.
        accounts = [
            ("Smoke Admin", ADMIN_EMAIL, ADMIN_PASSWORD, 1),
            ("Smoke Buyer", CUSTOMER_EMAIL, CUSTOMER_PASSWORD, 0),
            ("Smoke Other", OTHER_EMAIL, OTHER_PASSWORD, 0),
        ]
        for name, email, password, is_admin in accounts:
            execute(
                """INSERT INTO users (name, email, password, phone, is_admin)
                   VALUES (%s, %s, %s, '9000000000', %s)""",
                (name, email, generate_password_hash(password), is_admin),
            )

        print(f"\nDatabase ready. Products: "
              f"{query_all('SELECT COUNT(*) c FROM products')[0]['c']}")
        print("-" * 62)

    client = app.test_client()

    # =================================================================
    print("\n[1] Public pages")
    # =================================================================
    response = client.get("/")
    body = response.get_data(as_text=True)
    check("home page loads", response.status_code == 200)
    check("home shows the categories", "Shop by Category" in body)
    check("home shows featured products", "Featured Products" in body)

    response = client.get("/products")
    check("product list loads", response.status_code == 200)
    check("list shows product cards", "product-card" in
          response.get_data(as_text=True))
    check("pagination is present", "page-btn" in response.get_data(as_text=True))

    response = client.get("/products?q=laptop")
    body = response.get_data(as_text=True)
    check("search finds 'laptop'", "Vertex 14 Laptop" in body)
    check("search hides other products", "Nova X1 Smartphone" not in body)

    response = client.get("/products?category=audio")
    check("category filter works",
          "Pulse Wireless Earbuds" in response.get_data(as_text=True))

    check("sorting works", client.get("/products?sort=price_low").status_code == 200)
    check("price filter works",
          client.get("/products?min_price=100&max_price=2000").status_code == 200)
    check("page 2 works", client.get("/products?page=2").status_code == 200)

    response = client.get("/product/nova-x1-smartphone")
    check("product details loads", response.status_code == 200)
    check("details show the price", "18,999.00" in response.get_data(as_text=True))

    response = client.get("/product/this-does-not-exist")
    check("unknown product gives 404", response.status_code == 404)
    check("404 page is friendly", "Page not found" in response.get_data(as_text=True))

    # =================================================================
    print("\n[2] Registration and login")
    # =================================================================
    page = client.get("/register")
    token = token_of(page)
    response = client.post("/register", data={
        "csrf_token": token, "name": "Bad Input", "email": "not-an-email",
        "password": "x", "confirm_password": "y"})
    body = response.get_data(as_text=True)
    check("bad email is rejected", "valid email" in body)
    check("weak password is rejected", "6 characters" in body)
    check("password mismatch is rejected", "do not match" in body)

    page = client.get("/register")
    response = client.post("/register", data={
        "csrf_token": token_of(page), "name": "Duplicate", "email": CUSTOMER_EMAIL,
        "password": "test123", "confirm_password": "test123"},
        follow_redirects=True)
    check("duplicate email is blocked", "already exists" in
          response.get_data(as_text=True))

    new_email = f"smoke{run_id}@example.com"
    page = client.get("/register")
    response = client.post("/register", data={
        "csrf_token": token_of(page), "name": "Smoke Tester", "email": new_email,
        "password": "test123", "confirm_password": "test123"},
        follow_redirects=True)
    check("new account is created", "Account created" in
          response.get_data(as_text=True))

    client = app.test_client()
    page = client.get("/login")
    response = client.post("/login", data={
        "csrf_token": token_of(page), "email": CUSTOMER_EMAIL,
        "password": "wrong-password", "next": ""}, follow_redirects=True)
    check("wrong password is rejected", "Incorrect email or password" in
          response.get_data(as_text=True))

    page = client.get("/login")
    response = client.post("/login", data={
        "csrf_token": token_of(page), "email": CUSTOMER_EMAIL,
        "password": CUSTOMER_PASSWORD, "next": ""})
    check("login redirects", response.status_code == 302)
    check("navbar shows the user's name",
          "Smoke Buyer" in client.get("/").get_data(as_text=True))

    response = client.post("/cart/add", data={
        "csrf_token": "not-the-right-token", "product_id": 1, "quantity": 1})
    check("bad CSRF token is rejected (400)", response.status_code == 400)

    # =================================================================
    print("\n[3] Shopping cart")
    # =================================================================
    body = client.get("/cart").get_data(as_text=True)
    check("empty cart is handled nicely", "Your cart is empty" in body)

    page = client.get("/product/nova-x1-smartphone")
    token = token_of(page)
    response = client.post("/cart/add", data={
        "csrf_token": token, "product_id": 1, "quantity": 2})
    check("add to cart redirects", response.status_code == 302)
    check("cart badge counts 2",
          client.get("/api/cart-count").get_json()["count"] == 2)

    body = client.get("/cart").get_data(as_text=True)
    check("cart shows the product", "Nova X1 Smartphone" in body)
    check("cart shows the subtotal", "37,998.00" in body)

    client.post("/cart/add", data={"csrf_token": token, "product_id": 1, "quantity": 9999})
    check("cannot exceed the stock", client.get("/api/cart-count").get_json()["count"] == 2)

    client.post("/cart/add", data={"csrf_token": token, "product_id": 1, "quantity": 0})
    check("zero quantity is refused", client.get("/api/cart-count").get_json()["count"] == 2)

    page = client.get("/cart")
    token = token_of(page)
    item_ids = re.findall(r'name="item_id" value="(\d+)"', page.get_data(as_text=True))
    item_id = item_ids[0] if item_ids else None

    if item_id:
        client.post("/cart/update", data={
            "csrf_token": token, "item_id": item_id, "quantity": 9999})
        check("cannot update beyond stock",
              client.get("/api/cart-count").get_json()["count"] == 2)
        check("over-stock update warns the user", "left in stock" in
              client.get("/cart").get_data(as_text=True))

        client.post("/cart/update", data={
            "csrf_token": token, "item_id": item_id, "quantity": -5})
        check("negative quantity is refused", "cannot be negative" in
              client.get("/cart").get_data(as_text=True))

        client.post("/cart/update", data={
            "csrf_token": token, "item_id": item_id, "quantity": 1})
        check("quantity updates correctly",
              client.get("/api/cart-count").get_json()["count"] == 1)

        client.post("/cart/remove", data={"csrf_token": token, "item_id": item_id})
        check("remove works", client.get("/api/cart-count").get_json()["count"] == 0)

        client.post("/cart/add", data={"csrf_token": token, "product_id": 1, "quantity": 1})

    # =================================================================
    print("\n[4] Checkout")
    # =================================================================
    page = client.get("/checkout")
    token = token_of(page)
    check("checkout page loads", page.status_code == 200)
    check("payment options are shown", "Cash on Delivery" in
          page.get_data(as_text=True))

    response = client.post("/checkout", data={
        "csrf_token": token, "customer_name": "Test Buyer",
        "email": "buyer@example.com", "phone": "123",
        "address": "short", "city": "", "state": "", "pincode": "99",
        "payment_method": "Cash on Delivery"}, follow_redirects=True)
    body = response.get_data(as_text=True)
    check("bad phone is rejected", "10 digits" in body)
    check("short address is rejected", "full delivery address" in body)
    check("bad PIN code is rejected", "PIN code" in body)

    response = client.post("/checkout", data={
        "csrf_token": token, "customer_name": "Test Buyer",
        "email": "buyer@example.com", "phone": "9876543210",
        "address": "12 MG Road, Near Central Park, Sector 5",
        "city": "Bengaluru", "state": "Karnataka", "pincode": "560001",
        "payment_method": "Cash on Delivery"})
    check("valid order is accepted", response.status_code == 302)
    confirmation_url = response.headers.get("Location", "")
    check("redirects to the confirmation page", "/confirmation" in confirmation_url)

    body = client.get(confirmation_url).get_data(as_text=True)
    check("confirmation thanks the customer", "order is placed" in body)
    check("confirmation shows an order ID", "ORD-" in body)
    check("cart is emptied after the order",
          client.get("/api/cart-count").get_json()["count"] == 0)

    body = client.get("/orders").get_data(as_text=True)
    check("order history lists the order", "ORD-" in body)

    # =================================================================
    print("\n[5] Order privacy")
    # =================================================================
    other = app.test_client()
    page = other.get("/login")
    other.post("/login", data={
        "csrf_token": token_of(page), "email": OTHER_EMAIL,
        "password": OTHER_PASSWORD, "next": ""})
    check("another customer cannot open this order (404)",
          other.get(confirmation_url).status_code == 404)
    check("a customer cannot open the admin panel (403)",
          other.get("/admin").status_code == 403)
    check("403 page is friendly", "Access denied" in other.get("/admin").get_data(as_text=True))

    guest = app.test_client()
    check("logged-out visitor is sent to login",
          guest.get("/cart").status_code == 302)

    # =================================================================
    print("\n[6] Admin panel")
    # =================================================================
    admin = app.test_client()
    page = admin.get("/login")
    response = admin.post("/login", data={
        "csrf_token": token_of(page), "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD, "next": ""})
    check("admin logs in", response.status_code == 302)

    dashboard = admin.get("/admin")
    body = dashboard.get_data(as_text=True)
    check("dashboard loads", dashboard.status_code == 200)
    check("dashboard shows revenue", "Total revenue" in body)
    check("dashboard shows customer count", "Customers" in body)

    check("product list loads", admin.get("/admin/products").status_code == 200)
    check("order list loads", admin.get("/admin/orders").status_code == 200)
    check("status filter loads", admin.get("/admin/orders?status=Pending").status_code == 200)
    check("user list loads", admin.get("/admin/users").status_code == 200)

    body = admin.get("/admin/users").get_data(as_text=True)
    check("users are listed", CUSTOMER_EMAIL in body)
    check("passwords are never shown",
          "scrypt" not in body and "pbkdf2" not in body)

    # --- add a product ---
    page = admin.get("/admin/products/add")
    token = token_of(page)
    response = admin.post("/admin/products/add", data={
        "csrf_token": token, "name": "Smoke Test Widget",
        "description": "A product created by the smoke test script.",
        "price": "999.50", "stock": "7", "category_id": "1",
        "is_active": "1"})
    check("admin can add a product", response.status_code == 302)
    check("new product appears in the list",
          "Smoke Test Widget" in admin.get("/admin/products").get_data(as_text=True))

    response = admin.post("/admin/products/add", data={
        "csrf_token": token, "name": "Bad", "description": "short",
        "price": "abc", "stock": "-1", "category_id": "1"})
    check("invalid product is rejected",
          "price" in response.get_data(as_text=True).lower())

    # --- find and edit it ---
    match = re.search(r"/admin/products/edit/(\d+)",
                      admin.get("/admin/products?q=Smoke Test Widget").get_data(as_text=True))
    new_id = int(match.group(1)) if match else None
    check("new product id can be found", new_id is not None)

    if new_id:
        page = admin.get(f"/admin/products/edit/{new_id}")
        response = admin.post(f"/admin/products/edit/{new_id}", data={
            "csrf_token": token_of(page), "name": "Smoke Test Widget v2",
            "description": "The product name has now been updated.",
            "price": "1099.00", "stock": "3", "category_id": "1",
            "image_current": "placeholder.svg", "is_active": "1"})
        check("admin can edit a product", response.status_code == 302)
        check("edit is saved",
              "Smoke Test Widget v2" in admin.get("/admin/products").get_data(as_text=True))

        # --- delete it ---
        page = admin.get("/admin/products")
        response = admin.post(f"/admin/products/delete/{new_id}",
                              data={"csrf_token": token_of(page)})
        check("admin can delete a product", response.status_code == 302)
        check("deleted product gives 404",
              admin.get(f"/admin/products/edit/{new_id}").status_code == 404)

    # --- update an order status ---
    page = admin.get("/admin/orders")
    match = re.search(r"/admin/orders/(\d+)", page.get_data(as_text=True))
    if match:
        order_id = match.group(1)
        detail = admin.get(f"/admin/orders/{order_id}")
        response = admin.post("/admin/orders/update-status", data={
            "csrf_token": token_of(detail), "order_id": order_id, "status": "Shipped"})
        check("admin can update the order status", response.status_code == 302)
        detail = admin.get(f"/admin/orders/{order_id}")
        check("new status is saved", 'value="Shipped" selected' in
              detail.get_data(as_text=True))

        detail = admin.get(f"/admin/orders/{order_id}")
        admin.post("/admin/orders/update-status", data={
            "csrf_token": token_of(detail), "order_id": order_id, "status": "HACKED"})
        check("invalid status is refused",
              "Invalid order status" in
              admin.get("/admin/orders?status=Pending").get_data(as_text=True))

    # =================================================================
    print("\n[7] Security checks")
    # =================================================================
    attacker = app.test_client()
    page = attacker.get("/login")
    result = attacker.post("/login", data={
        "csrf_token": token_of(page),
        "email": "' OR '1'='1",
        "password": "' OR '1'='1",
        "next": ""}, follow_redirects=True)
    check("SQL injection in login is blocked", "Incorrect email or password" in
          result.get_data(as_text=True))
    check("SQL injection does not log anyone in",
          "Log out" not in attacker.get("/").get_data(as_text=True))

    injection = "'; DROP TABLE users; --".replace(" ", "%20")
    check("SQL injection in search is safe",
          client.get("/products?q=" + injection).status_code == 200)
    check("SQL injection in admin search is safe",
          admin.get("/admin/products?q=" + injection).status_code == 200)
    check("SQL injection in sort is safe",
          client.get("/products?sort=" + injection).status_code == 200)

    xss = "%3Cscript%3Ealert(1)%3C/script%3E"
    check("XSS in search is escaped",
          "<script>" not in client.get("/products?q=" + xss).get_data(as_text=True))
    check("XSS in the URL gives 404",
          client.get("/product/" + xss).status_code == 404)

    with app.app_context():
        from app import query_all
        tables = sorted(list(row.values())[0] for row in query_all("SHOW TABLES"))
    check("all 6 tables still exist", len(tables) == 6, str(tables))

    check("unknown URL gives 404", client.get("/no-such-page").status_code == 404)

    # =================================================================
    print("\n[8] Cleaning up")
    # =================================================================
    with app.app_context():
        from app import execute, query_all
        # The orders reference these users, so remove those first.
        execute("DELETE FROM order_items WHERE order_id IN "
                "(SELECT id FROM orders WHERE user_id IN "
                " (SELECT id FROM users WHERE email IN (%s, %s, %s)))",
                (ADMIN_EMAIL, CUSTOMER_EMAIL, OTHER_EMAIL))
        execute("DELETE FROM orders WHERE user_id IN "
                "(SELECT id FROM users WHERE email IN (%s, %s, %s))",
                (ADMIN_EMAIL, CUSTOMER_EMAIL, OTHER_EMAIL))
        execute("DELETE FROM cart_items WHERE user_id IN "
                "(SELECT id FROM users WHERE email IN (%s, %s, %s))",
                (ADMIN_EMAIL, CUSTOMER_EMAIL, OTHER_EMAIL))
        execute("DELETE FROM users WHERE email IN (%s, %s, %s)",
                (ADMIN_EMAIL, CUSTOMER_EMAIL, OTHER_EMAIL))
        execute("DELETE FROM products WHERE name LIKE %s", (f"{TEST_PRODUCT}%",))

        left = query_all("SELECT COUNT(*) c FROM users WHERE email LIKE %s",
                         ("smoke-%",))
    check("throwaway accounts removed", left[0]["c"] == 0, str(left[0]["c"]))

    # =================================================================
    print("\n" + "=" * 62)
    print(f"  PASSED : {len(passed)}")
    print(f"  FAILED : {len(failed)}")
    if failed:
        print("\n  Tests that failed:")
        for name in failed:
            print(f"    - {name}")
    print("=" * 62 + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())