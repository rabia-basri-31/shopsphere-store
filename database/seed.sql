-- =====================================================================
--  database/seed.sql
--  Fills the database with sample categories and products so the website
--  has something to show on the very first run.
--
--  HOW TO RUN IT (after schema.sql)
--      mysql -u root -p < database/seed.sql
--
--  NOTE: We do NOT create any user here. Use  python admin_setup.py
--  to create your own admin and customer accounts safely.
-- =====================================================================

USE ecommerce_db;

-- --- Categories -----------------------------------------------------
INSERT INTO categories (name, slug, description) VALUES
    ('Mobiles & Tablets', 'mobiles-tablets', 'Phones, tablets and accessories'),
    ('Laptops & Computers', 'laptops-computers', 'Laptops, monitors and PC parts'),
    ('Audio', 'audio', 'Headphones, earbuds and speakers'),
    ('Home & Kitchen', 'home-kitchen', 'Everyday things for your home'),
    ('Fashion', 'fashion', 'Clothing, shoes and accessories'),
    ('Books & Stationery', 'books-stationery', 'Books, notebooks and pens')
ON DUPLICATE KEY UPDATE description = VALUES(description);


-- --- Products -------------------------------------------------------
-- Every product below uses "placeholder.svg" as its image.
-- Replace it with your own picture from the admin panel later.

INSERT INTO products
    (name, slug, description, price, stock, image, category_id, is_featured)
VALUES
('Nova X1 Smartphone',
 'nova-x1-smartphone',
 '6.7 inch AMOLED display, 5000 mAh battery, 8 GB RAM and 128 GB storage. A fast everyday phone with a bright screen and clean software.',
 18999.00, 25, 'placeholder.svg', 1, 1),

('Pulse Wireless Earbuds',
 'pulse-wireless-earbuds',
 'True wireless earbuds with active noise cancellation, 30 hour battery life and a compact charging case that fits in your pocket.',
 2499.00, 60, 'placeholder.svg', 3, 1),

('Vertex 14 Laptop',
 'vertex-14-laptop',
 '14 inch laptop with 16 GB RAM, 512 GB SSD and a full HD display. Perfect for college assignments, coding and everyday office work.',
 54990.00, 12, 'placeholder.svg', 2, 1),

('Lumen Desk Lamp',
 'lumen-desk-lamp',
 'Adjustable LED desk lamp with three brightness levels. Helps you study late at night without straining your eyes.',
 1199.00, 40, 'placeholder.svg', 4, 0),

('Classic Denim Jacket',
 'classic-denim-jacket',
 'Comfortable cotton denim jacket with a modern slim fit. Works well over a t-shirt on cool days.',
 1799.00, 30, 'placeholder.svg', 5, 1),

('The Practical Programmer',
 'the-practical-programmer',
 'A beginner friendly programming book that explains real software projects step by step. A great first read for web development.',
 599.00, 80, 'placeholder.svg', 6, 0),

('Aero Running Shoes',
 'aero-running-shoes',
 'Lightweight running shoes with a cushioned sole and breathable mesh. Good for daily jogging and long walks.',
 3299.00, 22, 'placeholder.svg', 5, 1),

('Brew Master Coffee Maker',
 'brew-master-coffee-maker',
 'Compact coffee maker that brews two cups at a time. Includes a reusable steel filter and an automatic shut off.',
 2749.00, 18, 'placeholder.svg', 4, 1),

('Notebook Pack of 5',
 'notebook-pack-of-5',
 'Five A4 size lined notebooks with 200 pages each. Hard cover, spiral bound and fountain pen friendly.',
 349.00, 100, 'placeholder.svg', 6, 0),

('Echo Bluetooth Speaker',
 'echo-bluetooth-speaker',
 'Portable Bluetooth speaker with surprisingly loud sound, 12 hour play time and a strap you can hang anywhere.',
 1999.00, 35, 'placeholder.svg', 3, 0),

('Glow LED Monitor 24 inch',
 'glow-led-monitor-24-inch',
 '24 inch Full HD LED monitor with an anti glare screen. A simple and affordable second screen for study or work.',
 9899.00, 9, 'placeholder.svg', 2, 0),

('Zen Ceramic Mug Set',
 'zen-ceramic-mug-set',
 'Set of four stoneware mugs that are safe in the microwave and dishwasher. Nice simple shapes in matte colours.',
 899.00, 45, 'placeholder.svg', 4, 0);