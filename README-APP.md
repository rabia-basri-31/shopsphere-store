# ShopSphere — E-Commerce Web Application

A complete, working e-commerce website built for a **Web Developer fresher portfolio**.

**Stack:** HTML5 · CSS3 · Vanilla JavaScript · Python Flask · MySQL · Git

This project is deliberately beginner-friendly: one main `app.py`, no frameworks
beyond Flask, no JavaScript build tools, and clear comments everywhere.

---

## Table of contents

1. [What this project does](#1-what-this-project-does)
2. [Tech stack](#2-tech-stack)
3. [Features](#3-features)
4. [Project structure](#4-project-structure)
5. [Prerequisites](#5-prerequisites)
6. [Setup (step by step)](#6-setup-step-by-step)
7. [Database setup](#7-database-setup)
8. [Creating your accounts](#8-creating-your-accounts)
9. [Running the project](#9-running-the-project)
10. [Testing checklist](#10-testing-checklist)
11. [Security implemented](#11-security-implemented)
12. [Git and GitHub](#12-git-and-github)
13. [Troubleshooting](#13-troubleshooting)
14. [Project explanation for an interview](#14-project-explanation-for-an-interview)
15. [20 interview questions and answers](#15-20-interview-questions-and-answers)

---

## Screenshots

| Home | Products |
|---|---|
| ![Home](docs/screenshots/01-home.png) | ![Products](docs/screenshots/02-products.png) |

| Product details | Cart |
|---|---|
| ![Product details](docs/screenshots/03-product.png) | ![Cart](docs/screenshots/08-cart.png) |

| Checkout | Admin dashboard |
|---|---|
| ![Checkout](docs/screenshots/09-checkout.png) | ![Admin dashboard](docs/screenshots/10-admin-dashboard.png) |

More: [About](docs/screenshots/04-about.png) ·
[Contact](docs/screenshots/05-contact.png) ·
[Admin products](docs/screenshots/11-admin-products.png) ·
[404 page](docs/screenshots/07-404.png)

---

## Demo accounts

This is a **demo store**. No payment is processed and no order is ever
shipped.

The database is **never uploaded to GitHub** (it is a local MySQL server),
so nobody else can log in. If you deploy this to a public host, use your own
accounts and change the passwords first — never publish real credentials.

Create your own accounts at any time:

```bash
python admin_setup.py
```

Then log in at `/login`. Admins are sent straight to `/admin`.

---

## 1. What this project does

ShopSphere is a full shopping website. A visitor can browse products, search,
filter, register, log in, add items to a cart and place an order. An
administrator has a separate dashboard where they can add, edit and hide
products, view customers and update order statuses.

Checkout is a **mock/demo** flow — there is no real payment gateway and no money
changes hands. It behaves like a Cash-on-Delivery order.

---

## 2. Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | HTML5, CSS3, Vanilla JS | No build step, easy to read |
| Layout | CSS Grid + Flexbox + media queries | Responsive without a framework |
| Templates | Jinja2 (comes with Flask) | Server-side rendering |
| Backend | Python 3.10+ / Flask 3.1 | Lightweight, beginner-friendly |
| Database | MySQL 8.x | Industry-standard relational DB |
| DB driver | `mysql-connector-python` | The official MySQL driver |
| Secrets | `python-dotenv` | Keeps credentials out of the code |
| Version control | Git + GitHub | Portfolio hosting |

---

## 3. Features

### Customers
- **Home page** — hero banner, category grid, featured products, new arrivals, footer
- **Search** — by keyword, across name and description
- **Filter** — by category, by minimum/maximum price, plus 4 sort options
- **Pagination** — 9 products per page
- **Product details** — image, description, price, live stock status, related products
- **Register / Login / Logout** with server-side validation
- **Shopping cart** — add, change quantity, remove one item, empty the cart
- **Stock protection** — cannot add or keep more items than exist
- **Checkout** — delivery form, bill summary, mock payment method
- **Order history** — list of past orders with a progress bar
- **Invoice** — printable order page

### Admin panel
- **Dashboard** — customers, products, orders, pending orders, total revenue
- **Best sellers** and **low stock alerts**
- **Add / Edit / Delete products**, with image upload
- **View users** with order count and total spent
- **View all orders**, filter by status
- **Update order status** — Pending → Paid → Packed → Shipped → Delivered / Cancelled

### Quality
- Fully responsive (desktop / tablet / mobile)
- Custom 400 / 403 / 404 / 500 / 503 error pages
- Friendly flash messages for every action
- Server-side log file at `logs/error.log`
- Lighthouse scores: **Accessibility 100, Best Practices 100, SEO 100**

---

## 4. Project structure

```
ecommerce-web-app/
│
├── app.py                  # Main file: routes, DB helpers, security, error handling
├── config.py               # All settings, read from environment variables
├── admin_setup.py          # One-time script to create admin / customer accounts
├── requirements.txt        # Python packages needed
├── .env.example            # Template for .env  (safe to commit)
├── .gitignore              # Stops .env / .venv / logs being committed
├── README.md               # This file
│
├── templates/
│   ├── base.html           # Main layout: navbar, footer, flash messages
│   ├── macros.html         # Reusable HTML blocks (product card, badge, pagination)
│   ├── index.html          # Home page
│   ├── products.html       # Listing + search + filters
│   ├── product_details.html# One product
│   ├── login.html          # Log in
│   ├── register.html       # Create account
│   ├── cart.html           # Shopping cart
│   ├── checkout.html       # Mock checkout
│   ├── orders.html         # Order history
│   ├── order_details.html  # Invoice / confirmation
│   │
│   ├── admin/
│   │   ├── _layout.html        # Admin layout with dark sidebar
│   │   ├── dashboard.html      # Admin home
│   │   ├── products.html       # Manage all products
│   │   ├── _product_form.html  # Shared add/edit form
│   │   ├── add_product.html
│   │   ├── edit_product.html
│   │   ├── orders.html         # All orders + status filter
│   │   ├── order_details.html  # One order + change status
│   │   └── users.html          # All registered users
│   │
│   └── errors/
│       ├── 400.html          # Bad request (usually an expired form)
│       ├── 403.html          # Not allowed
│       ├── 404.html          # Page not found
│       └── 500.html          # Server / database error
│
├── static/
│   ├── css/style.css       # Whole design system, 4 responsive breakpoints
│   ├── js/script.js        # 12 small progressive-enhancement features
│   └── images/
│       ├── placeholder.svg # Shown when a product has no photo yet
│       └── uploads/        # Product images uploaded by the admin
│
├── database/
│   ├── schema.sql          # Creates database + all 6 tables
│   └── seed.sql            # Sample categories and products
│
├── tests/
│   └── smoke_test.py       # 83 automatic checks of every feature
│
├── tools/
│   └── generate_product_images.py   # Draws the product illustrations
│
├── logs/                   # Created automatically, holds error.log
└── .venv/                  # Python virtual environment (never committed)
```

---

## 5. Prerequisites

Install these first:

| Software | Version | Check with |
|---|---|---|
| Python | 3.10 or newer | `python --version` |
| MySQL Server | 8.0 or newer | `mysql --version` |
| Git | any recent | `git --version` |

---

## 6. Setup (step by step)

### Step 1 — Open a terminal in the project folder

```bash
cd ecommerce-web-app
```

### Step 2 — Create a virtual environment

A virtual environment keeps this project's packages separate from your other
Python projects.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now start with `(.venv)`.

> **If PowerShell blocks activation**, run this once:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### Step 3 — Install the packages

```bash
pip install -r requirements.txt
```

Expected output ends with something like:
`Successfully installed Flask-3.1.0 mysql-connector-python-9.1.0 ...`

### Step 4 — Create your `.env` file

The `.env` file holds your secret key and database password. It is **never**
uploaded to GitHub (that is what `.gitignore` is for).

**Windows (PowerShell):**
```powershell
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Now open `.env` and set at least `SECRET_KEY` and `DB_PASSWORD`.

Generate a strong secret key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5 — Set up MySQL

See [section 7](#7-database-setup).

---

## 7. Database setup

### 7.1 Start MySQL

**Windows:** open **Services** (`services.msc`), find `MySQL80` / `MySQL84`, set
it to **Automatic**, and start it. Or from an admin PowerShell:
```powershell
net start MySQL84
```

**macOS (Homebrew):** `brew services start mysql`
**Linux:** `sudo systemctl start mysql`

### 7.2 Run the two SQL files

Open a terminal in the project folder.

**Windows:**
```powershell
mysql -u root -p < database\schema.sql
mysql -u root -p < database\seed.sql
```

**macOS / Linux:**
```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

Or in **MySQL Workbench**: double-click each `.sql` file and press the ⚡ lightning
bolt.

### What this creates

| Table | Purpose |
|---|---|
| `categories` | Product groups (name + URL slug) |
| `users` | Customers and admins (`is_admin` decides the role) |
| `products` | Everything for sale |
| `cart_items` | One row per product in a user's cart |
| `orders` | One row per placed order |
| `order_items` | The individual products inside an order |

`schema.sql` also creates a **limited database user** `ecommerce_user` that can
only `SELECT / INSERT / UPDATE / DELETE` inside `ecommerce_db` — safer than
letting the website connect as `root`. Change the password in `schema.sql`
before running it if you prefer.

### 7.3 Confirm it worked

```powershell
mysql -u ecommerce_user -p -e "USE ecommerce_db; SHOW TABLES; SELECT COUNT(*) FROM products;"
```

You should see 6 tables and 12 products.

---

## 8. Creating your accounts

There is **no hard-coded admin password** in the code. Create accounts with the
provided script instead:

```bash
python admin_setup.py
```

Choose:
- `1` = admin account
- `2` = customer account
- `3` = one of each

The script asks for a password (hidden as you type), checks its strength, hashes
it, and saves it safely.

---

## 9. Running the project

```bash
python app.py
```

Open your browser at:

> **http://127.0.0.1:5000**

Press `Ctrl + C` in the terminal to stop the server.

### To view it on your phone

The app runs on `0.0.0.0:5000`, so any device on the same Wi-Fi can reach it.

```powershell
ipconfig
```

Find your IPv4 address (e.g. `192.168.1.5`) and open
`http://192.168.1.5:5000` on the phone.

### Common way to log in

Admins are redirected to `/admin` automatically. Use the accounts you created
with `python admin_setup.py` — no default credentials are shipped with this
project.

---

## 10. Testing checklist

### 10.1 Run the automated tests first

```bash
python tests/smoke_test.py
```

This walks through every feature — browsing, search, filters, registration,
login, cart limits, checkout, order privacy, the admin panel, and a set of
SQL-injection / XSS / CSRF attacks — and prints `PASS` or `FAIL` for each check.

Expected: **83 passed, 0 failed.**

The script needs nothing from you: it creates its own throwaway accounts, runs
everything, then deletes them again, so your database is left exactly as it
found it.

---

### 10.2 Regenerate the product pictures

The shop ships with 12 hand-drawn SVG illustrations so nothing shows a grey
placeholder. They are generated by a script, not made by hand:

```bash
python tools/generate_product_images.py
```

Want to change the colours? Edit `CATEGORY_THEME` near the top of that file and
run it again. It only ever rewrites these 12 illustrations — it never touches
photos you upload yourself through the admin panel.

---

### 10.3 Then check it in the browser

Go through this before you call the project done.

**Home & browsing**
- [ ] Home page shows 6 categories and 5 featured products
- [ ] Search `laptop` in the navbar → only laptop products appear
- [ ] Category filter and price filter both work
- [ ] Sort "Price: low to high" reorders correctly
- [ ] Pagination works and the filters survive page changes
- [ ] A product with stock `0` shows "Out of stock"

**Authentication**
- [ ] Register with a bad email → friendly error
- [ ] Register with a weak password → friendly error
- [ ] Register with an existing email → "already exists"
- [ ] Log in with a wrong password → "Incorrect email or password"
- [ ] Log in with the correct password → welcome message

**Cart**
- [ ] Add to cart → green message and badge count increases
- [ ] Add more than the stock allows → refused with a clear message
- [ ] Change quantity → total updates
- [ ] Set quantity to 0 → item is removed
- [ ] Empty Cart removes everything

**Checkout**
- [ ] Checkout with an empty cart → redirected back to the cart
- [ ] Enter a bad phone/PIN → friendly errors
- [ ] Enter valid details → order placed, order ID shown
- [ ] Stock numbers in the admin panel went **down**
- [ ] Cart is now empty

**Orders**
- [ ] `My Orders` lists the order with a progress bar
- [ ] Order details shows the invoice (Print Invoice works)
- [ ] Logging in as another customer does **not** show this order

**Admin**
- [ ] Logged-in customer visiting `/admin` → "Access denied" 403 page
- [ ] Admin dashboard shows revenue and customer counts
- [ ] Add a product → it appears in the shop
- [ ] Edit a product → change shows on the shop
- [ ] Delete an unused product → gone
- [ ] Delete a product that was already ordered → archived, orders still correct
- [ ] Change an order status → the customer sees the new status
- [ ] `Users` page lists customers but **never** shows a password

**Responsive** (use your browser's device toolbar, `F12`)
- [ ] 375px wide: hamburger menu appears and opens
- [ ] 768px wide: 2-column product grid, filters on top
- [ ] 1024px wide: 3 columns, sidebar visible
- [ ] Cart stacks vertically on mobile

---

## 11. Security implemented

| Risk | Protection | Where |
|---|---|---|
| Crash if JavaScript is off | Content is visible by default; JS only *adds* polish | `script.js` |
| Broken images shipping silently | Generator validates every SVG before writing it | `tools/` |
| Password theft | Hashed with Werkzeug (salt + scrypt) | `app.py` register/login |
| Database credentials | Stored in `.env`, gitignored | `config.py` |
| Session tampering | `SECRET_KEY` signs the cookie | `config.py` |
| SQL injection | **100% parameterised queries** | `query_all` / `query_one` / `execute` |
| SQL injection via sort | Value mapped through a whitelist dict | `products()` |
| Cross-site request forgery | CSRF token on every POST | `protect_from_csrf()` |
| XSS | Jinja2 autoescaping on every output | all templates |
| Privilege escalation | `@admin_required` on all admin routes | `app.py` |
| Broken object access | Order queries always filter by `user_id` | `get_order_for_user()` |
| Open redirect | `next` must start with `/` and not `//` | `safe_next_url()` |
| Account enumeration | Same message for bad email and bad password | `login()` |
| Overselling | Stock re-checked inside a transaction with `FOR UPDATE` | `place_order()` |
| Product images | Real photos via `images.unsplash.com` direct URLs, plus an `onerror` fallback to `placeholder.svg` | `macros.html` |
| Insecure file upload | Extension whitelist + random filename + 2 MB limit | `save_product_image()` |
| Crashes | try/except + friendly 500 page + `logs/error.log` | `app.py` |
| Blank page if JS fails | Content visible by default; JS only *adds* polish | `script.js` |

---

## 12. Git and GitHub

### First upload

```bash
git init
git add .
git commit -m "Initial commit: Flask + MySQL e-commerce application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ecommerce-web-app.git
git push -u origin main
```

Create the empty repository on GitHub **first** (with no README), then run the
above.

### Everyday commands

```bash
git status                  # see what changed
git add .                   # stage everything
git commit -m "Add product search"
git push                    # upload
```

### Good commit messages

```
Add product image upload to admin panel
Fix stock calculation on checkout page
Improve mobile layout for cart table
```

### Before you push — check this

```bash
git status
```

`.env`, `.venv/`, `logs/` and `__pycache__/` must **not** appear in the list.
If they do, `.gitignore` is missing or broken — remove them with
`git rm -r --cached .env`.

---

## 13. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | venv not active, or packages missing | Activate `.venv`, then `pip install -r requirements.txt` |
| `Can't connect to local MySQL server` | MySQL service stopped | Start the MySQL service, or `net start MySQL84` |
| `Access denied for user 'ecommerce_user'` | Wrong password in `.env` | Re-run `schema.sql`, or fix `DB_PASSWORD` |
| `Unknown database 'ecommerce_db'` | `schema.sql` not run yet | `mysql -u root -p < database/schema.sql` |
| Page shows "We could not reach the database" | MySQL down or bad `.env` | Check both; see `logs/error.log` |
| `403 Forbidden` on `/admin` | Not logged in as an admin | Run `python admin_setup.py` and choose option 1 |
| Changes to templates not showing | Flask caches templates when debug is off | Set `FLASK_DEBUG=true` in `.env`, then `Ctrl+C` and `python app.py` again |
| `.env` changes ignored | Environment variables already loaded | Restart the server |
| Port 5000 already in use | Another program on that port | `netstat -ano | findstr :5000` then stop it, or set `PORT=5001` in `.env` |
| `₹` shows as `?` | File not saved as UTF-8 | Save `.env` as UTF-8, or remove `CURRENCY` and use the default |
| PowerShell blocks `Activate.ps1` | Execution policy | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| Image upload rejected | Wrong type or over 2 MB | Use JPG/PNG/GIF/WEBP under 2 MB |

---

## 14. Project explanation for an interview

> **"Tell me about your e-commerce project."**
>
> I built a complete shopping website called ShopSphere using Python Flask, MySQL,
> vanilla HTML/CSS/JavaScript and Git. It has a customer-facing shop and a
> separate admin panel.
>
> **Architecture.** The client sends an HTTP request. Flask's routing layer
> (`app.py`) matches it to a function. That function runs a parameterised SQL
> query through one of three small helpers, gets the data, and passes it to a
> Jinja2 template. Jinja2 merges that template with `base.html` and sends back
> finished HTML. The browser then runs JavaScript only for convenience
> behaviours — everything important happens on the server.
>
> **Database.** Six tables with proper primary keys, foreign keys and
> constraints. Two deliberate design decisions: (1) `order_items` stores a *copy*
> of the product name and price, so renaming or repricing a product later never
> corrupts an old invoice; (2) `products` has a soft-delete flag, so a product
> that was already ordered is hidden from the shop instead of being deleted.
>
> **Security.** Passwords are hashed with Werkzeug's salted scrypt — I never
> store plain text. Every SQL query is parameterised, which is what prevents SQL
> injection. I added CSRF tokens to every form. Order pages always filter by the
> logged-in user's id, so guessing a URL cannot expose somebody else's order.
> Admin routes have a decorator that checks `is_admin` before the function runs.
> Database credentials come from environment variables via `.env`, which is
> gitignored so secrets never reach GitHub.
>
> **Data integrity.** Checkout runs inside a database transaction with
> `SELECT ... FOR UPDATE`. The stock is re-checked and re-locked at that exact
> moment, so two people buying the last item cannot both succeed. If anything
> fails, `rollback()` undoes the whole order instead of leaving half an order
> behind.
>
> **Responsive UI.** Pure CSS Grid and Flexbox with four breakpoints at 1024px,
> 900px, 640px and 400px. The product grid uses `repeat(auto-fill, minmax(240px,
> 1fr))`, which makes it responsive in one line. Mobile users get a hamburger
> menu and stacked tables. Lighthouse scores 100 for accessibility, best
> practices and SEO.
>
> **Error handling.** Custom pages for 400, 403, 404, 500 and 503. Every
> database call is wrapped so a failure shows a friendly message and writes the
> details to `logs/error.log` instead of crashing the site.
>
> **What I'd improve next.** Move the routes into Flask Blueprints, add
> server-side caching for the product list, add an image-resizing step on
> upload, and write unit tests with `pytest`.

---

## 15. 20 interview questions and answers

### 1. What is Flask? Why did you choose it?
Flask is a Python web framework (a *microframework*) that handles HTTP
requests, routing and templates. I chose it because it is small, has no
mandatory configuration, and its code reads almost like plain Python — which
made the project easy to explain and debug.

### 2. What is a template and how does Jinja2 work?
A template is an HTML file with placeholders. Jinja2 fills them with data at
request time and sends finished HTML to the browser. I used `{% extends
"base.html" %}` so the navbar and footer are written once instead of being copied
into 16 files.

### 3. What is the difference between `GET` and `POST`?
`GET` reads data and can be bookmarked or cached. `POST` changes data — it is
used for login, forms and payments. In this project every data-changing action
(add to cart, delete product, update status) is a `POST`.

### 4. How does your application talk to MySQL?
Through `mysql-connector-python`. `app.py` opens one connection per request and
reuses it via Flask's `g` object, then closes it in a `teardown` hook. All SQL
goes through three helpers: `query_all`, `query_one` and `execute`.

### 5. What is SQL injection and how did you prevent it?
SQL injection happens when user input is glued into SQL as code. Typing
`' OR '1'='1` into a login box could otherwise bypass the whole check. I pass
every value as a parameter instead:

```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

MySQL treats `email` as plain data, never as part of the query. I also mapped
the sort parameter through a whitelist dictionary so it can only ever be one of
four known strings.

### 6. How do you store passwords?
I hash them with `werkzeug.security.generate_password_hash()`, which uses
**scrypt** with a random salt. The salt means two users with the same password
get different hashes. Login uses `check_password_hash()`, which re-hashes and
compares in constant time. The plain password is never stored or logged.

### 7. What is a session?
A session is Flask's way of remembering a logged-in user between requests. It is
stored server-side and the browser only keeps a signed cookie holding a session
id. Because the cookie is signed with `SECRET_KEY`, it cannot be tampered with.

### 8. How does admin authorization work?
There are two decorators, `login_required` and `admin_required`.
`admin_required` first checks that someone is logged in, then checks
`is_admin == 1`, and only then calls the view. A customer who reaches `/admin`
gets a 403 page, and the attempt is written to the log. Crucially, the check is
in the decorator, so a new admin route cannot accidentally be left unprotected.

### 9. What is CSRF and how did you prevent it?
CSRF is when another website tricks your browser into submitting a form to mine —
for example, placing an order without the user's knowledge. I generate a random
token per session and put it in every form as a hidden field. On every POST,
`protect_from_csrf()` compares it to the session value and rejects the request
with a 400 page if they differ.

### 10. What is XSS and how did you prevent it?
XSS is when user input is echoed back as HTML and runs as script. Jinja2 escapes
`{{ variable }}` automatically, so `<script>` becomes harmless text. I never use
the `| safe` filter, and the same test proved a `<script>` payload stored in the
database renders as plain text.

### 11. What is a database transaction and why did you use one?
A transaction groups several statements so they all succeed or all fail. Checkout
inserts an order, inserts its items, reduces stock and empties the cart. If any
step failed, the customer would get an order with no items. So I wrap it in a
transaction and call `rollback()` on error.

### 12. What does `SELECT ... FOR UPDATE` do?
It locks the matching rows until the transaction ends. At checkout I re-read the
cart with this lock and re-check the stock at that exact moment. Without it, two
people could both buy the last item — both would pass the check and stock would
go negative. With it, the second transaction has to wait, then sees the reduced
stock and is rejected. This is called preventing a *race condition*.

### 13. Why store product name and price again in `order_items`?
Because the invoice must stay correct forever. If I stored only `product_id` and
joined the table, then changing a product's price tomorrow would silently change
what past customers were charged. Storing a copy (a *denormalisation* /
*historical snapshot*) means old invoices always show the real price paid.

### 14. What is a foreign key? Give an example.
A foreign key is a column that points to another table's primary key, enforcing
referential integrity. `products.category_id` points to `categories.id`. MySQL
refuses to insert a product with a category that does not exist.
`order_items.order_id` uses `ON DELETE CASCADE`, so deleting an order also
deletes its item rows and never leaves orphans.

### 15. What is soft delete, and why did you use it?
Soft delete means marking a record as inactive instead of removing the row. In
the admin panel, if a product has already been ordered, deleting it would damage
order history, so I set `is_active = 0` and hide it from the shop instead. The
product still appears correctly on old invoices.

### 16. What is normalization, and how far did you take it?
Normalization means organising tables to reduce duplicated data. I used it:
categories, products and users are separate tables, and `products.category_id`
replaces a repeated category name. I deliberately stopped short of full
normalization with `order_items`, because duplicating the product name and price
is the right trade-off there — denormalizing for correct historical invoices is
worth more than theoretical purity.

### 17. How does your search work?
The products route reads `q`, `category`, `min_price`, `max_price` and `sort`
from the URL, then builds the `WHERE` clause step by step, appending a condition
and its parameter together:

```python
if search_text:
    conditions.append("(p.name LIKE %s OR p.description LIKE %s)")
    params.extend([f"%{search_text}%"] * 2)
```

The count for pagination uses the same `WHERE` clause, so the totals can never
disagree with the results.

### 18. How is the site made responsive?
Pure CSS, no framework. I use CSS Grid and Flexbox with media queries at 1024px,
900px, 640px and 400px. The product grid is a single line —
`grid-template-columns: repeat(auto-fill, minmax(240px, 1fr))` — which makes it
fill the available width and wrap automatically. Under 900px the navbar collapses
into a hamburger menu and the cart table switches to stacked rows with
`grid-template-columns: 1fr`.

### 19. How do you handle errors?
Every database call is wrapped in `try/except`, and any error is written to
`logs/error.log` with a timestamp and written with `logger.error()`. Custom error
pages exist for 400, 403, 404, 500 and 503, so users see a friendly message
instead of a raw stack trace. A missing product calls `abort(404)` rather than
crashing, and an empty cart is treated as a normal state, not an error.

### 20. If you had to add a feature tomorrow, what would you change first?
Two things. First, I would split `app.py` into Flask Blueprints — one file for
auth, one for products, one for cart, one for admin. The code already separates
them with clear sections, so the move is mechanical and would make it far easier
to maintain. Second, I would add `pytest` unit tests for the price, stock and
password logic, because those are the parts where a mistake costs real money.
I would also cache the product list and add image resizing on upload.

---

## Licence

This project is for **learning and portfolio purposes only**.