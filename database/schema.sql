-- =====================================================================
--  database/schema.sql
--  Creates the database and every table for the e-commerce app.
--
--  HOW TO RUN IT
--     Open a terminal and run:
--         mysql -u root -p < database/schema.sql
--
--  (In MySQL Workbench you can also just double-click this file.)
-- =====================================================================

-- 1. Create the database.
--    utf8mb4 lets us store any text, including emoji and ₹ symbol.
CREATE DATABASE IF NOT EXISTS ecommerce_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Tell MySQL to use that database for everything below.
USE ecommerce_db;


-- =====================================================================
--  Table 1: categories
--  The product groups shown on the home page (Mobiles, Books, ...).
-- =====================================================================
CREATE TABLE IF NOT EXISTS categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL UNIQUE,
    slug        VARCHAR(120)  NOT NULL UNIQUE,   -- URL friendly name
    description VARCHAR(255)  DEFAULT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;


-- =====================================================================
--  Table 2: users
--  Stores customers AND the admin. The is_admin column decides the role.
--  NOTE: the password column stores a HASH, never the real password.
-- =====================================================================
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)  NOT NULL,
    email      VARCHAR(150)  NOT NULL UNIQUE,
    password   VARCHAR(255)  NOT NULL,          -- hashed, not plain text
    phone      VARCHAR(20)   DEFAULT NULL,
    address    TEXT          DEFAULT NULL,
    is_admin   TINYINT(1)    NOT NULL DEFAULT 0, -- 1 = admin, 0 = customer
    created_at TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- A customer must give a name, a valid-looking email and a password.
    CONSTRAINT chk_users_email CHECK (email LIKE '%_@_%._%')
) ENGINE = InnoDB;


-- =====================================================================
--  Table 3: products
--  Every item that can be bought in the shop.
-- =====================================================================
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200)   NOT NULL,
    slug        VARCHAR(220)   NOT NULL UNIQUE,   -- used in the URL
    description TEXT           DEFAULT NULL,
    price       DECIMAL(10, 2) NOT NULL,          -- e.g. 24999.00
    stock       INT            NOT NULL DEFAULT 0,
    image       VARCHAR(255)   DEFAULT NULL,      -- file name in static/images
    category_id INT            DEFAULT NULL,
    is_featured TINYINT(1)     NOT NULL DEFAULT 0,-- shown on home page
    is_active   TINYINT(1)     NOT NULL DEFAULT 1,-- 0 = hidden from shop
    created_at  TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

    -- FOREIGN KEY: a product must belong to an existing category.
    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    -- The price can never be negative, stock can never be negative.
    CONSTRAINT chk_products_price CHECK (price >= 0),
    CONSTRAINT chk_products_stock CHECK (stock >= 0)
) ENGINE = InnoDB;


-- =====================================================================
--  Table 4: cart_items
--  The shopping cart of each logged-in user.
--  A user can only have ONE row per product (see the UNIQUE key) -
--  that is why "add to cart" increases the quantity instead of
--  creating a duplicate row.
-- =====================================================================
CREATE TABLE IF NOT EXISTS cart_items (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    product_id INT NOT NULL,
    quantity   INT NOT NULL DEFAULT 1,
    added_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cart_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE   -- delete the cart rows when a user is deleted
        ON UPDATE CASCADE,

    CONSTRAINT fk_cart_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT uq_cart_user_product UNIQUE (user_id, product_id),
    CONSTRAINT chk_cart_quantity CHECK (quantity > 0)
) ENGINE = InnoDB;


-- =====================================================================
--  Table 5: orders
--  One row = one order placed by one customer at checkout.
--  The customer details are COPIED here on purpose: if the user later
--  edits their address we must not rewrite the history of past orders.
-- =====================================================================
CREATE TABLE IF NOT EXISTS orders (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    order_code     VARCHAR(25)  NOT NULL UNIQUE,  -- e.g. ORD-260106-4F7A
    user_id        INT          NOT NULL,
    customer_name  VARCHAR(100) NOT NULL,
    email          VARCHAR(150) NOT NULL,
    phone          VARCHAR(20)  NOT NULL,
    address        TEXT         NOT NULL,
    city           VARCHAR(80)  NOT NULL,
    state          VARCHAR(80)  NOT NULL,
    pincode        VARCHAR(10)  NOT NULL,
    payment_method VARCHAR(50)  NOT NULL DEFAULT 'Cash on Delivery',
    total_amount   DECIMAL(10, 2) NOT NULL,
    status         VARCHAR(30)  NOT NULL DEFAULT 'Pending',
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT chk_orders_total CHECK (total_amount >= 0)
) ENGINE = InnoDB;


-- =====================================================================
--  Table 6: order_items
--  The individual products inside one order.
--  We store product_name and price COPIES so the invoice stays correct
--  even if the product is renamed, repriced or deleted later.
-- =====================================================================
CREATE TABLE IF NOT EXISTS order_items (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT            NOT NULL,
    product_id   INT            DEFAULT NULL,
    product_name VARCHAR(200)   NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,   -- price at the time of purchase
    quantity     INT            NOT NULL,

    CONSTRAINT fk_items_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE    -- deleting an order deletes its items
        ON UPDATE CASCADE,

    CONSTRAINT fk_items_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE SET NULL   -- keep the invoice even if product is deleted
        ON UPDATE CASCADE,

    CONSTRAINT chk_items_quantity CHECK (quantity > 0)
) ENGINE = InnoDB;


-- =====================================================================
--  OPTIONAL (but recommended) - a limited MySQL user for the web app
-- ---------------------------------------------------------------------
--  Instead of letting the website log in as 'root' (which can DROP
--  every database on the computer), we create a small user that can
--  only read and change rows inside ecommerce_db.
--
--  >>> CHANGE THE PASSWORD BELOW BEFORE YOU RUN THIS FILE <<<
--
--  Pick your own password and use the EXACT SAME one on the
--  DB_PASSWORD line of your .env file.
--
--  If you prefer to use root, simply put DB_USER=root in your .env
--  and skip this whole section.
-- =====================================================================

CREATE USER IF NOT EXISTS 'ecommerce_user'@'localhost'
    IDENTIFIED BY 'CHANGE_THIS_TO_YOUR_OWN_PASSWORD';

-- Only these four permissions, and only on our one database.
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce_db.* TO 'ecommerce_user'@'localhost';

FLUSH PRIVILEGES;

-- Changing your mind about the password later? Run this:
--   ALTER USER 'ecommerce_user'@'localhost'
--       IDENTIFIED BY 'your_new_password';
--   FLUSH PRIVILEGES;


-- =====================================================================
--  Handy extra: the order statuses the admin can choose.
--  (Kept as a comment so beginners see the full list.)
--
--    Pending  -> Paid   -> Packed   -> Shipped   -> Delivered
--    Cancelled
-- =====================================================================