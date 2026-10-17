# M2 – Checkout & Order Placement

#### 2.1 `shipping_cost(subtotal)` → *(Noor)*
**Technique:** BVA around 0 and 999.00 (this is the best BVA example in the project).

| ID | Subtotal | Expected |
|----|----------|----------|
| CH-S1 | `-5` | 0.00 |
| CH-S2 | `0` | 0.00 |
| CH-S3 | `0.01` | 79.00 |
| CH-S4 | `998.99` | 79.00 |
| CH-S5 | `999.00` | 0.00 |
| CH-S6 | `999.01` | 0.00 |
| CH-S7 | `5000` | 0.00 |
| CH-S8 | `500` (typical) | 79.00 |

#### 2.2 `get_cart_items()` → *(Noor)* – mock `query_all`, `session`
| ID | Scenario | Expected |
|----|----------|----------|
| CH-C1 | Empty cart | `[]` |
| CH-C2 | 1 item, price 100, qty 3 | `line_total == 300` |
| CH-C3 | qty == stock | `is_out_of_stock` False |
| CH-C4 | qty = stock + 1 | `is_out_of_stock` True |
| CH-C5 | stock = 0 | True |
| CH-C6 | `is_active = 0` (archived) | True |
| CH-C7 | Multiple items | list length & order preserved |
| CH-C8 | Price as Decimal string `"19.99"` × 3 | exactly `59.97` (no float error) |

#### 2.3 `checkout()` route validation → *(Rabia)*
**Technique:** ECP + BVA on each field; decision table for "one field wrong at a time".

Valid baseline: name `Ali Khan`, email `ali@example.com`, phone `3001234567`, address `House 12, Street 4`, city `Lahore`, state `Punjab`, pincode `540000`, payment `Cash on Delivery`.

| ID | Scenario | Expected |
|----|----------|----------|
| CH-V1 | Empty cart | redirect `/cart`, warning |
| CH-V2 | Cart has out-of-stock item | redirect `/cart`, "update your cart first" |
| CH-V3 | All valid | `place_order` called, redirect to confirmation |
| CH-V4 | Phone 9 / 10 / 11 digits | reject / accept / reject |
| CH-V5 | Pincode 5 / 6 / 7 digits | reject / accept / reject |
| CH-V6 | Address 9 / 10 chars | reject / accept |
| CH-V7 | City 1 / 2 chars | reject / accept |
| CH-V8 | Invalid payment method `Bitcoin` | "valid payment method" |
| CH-V9 | Invalid email | "valid email address" |
| CH-V10 | All fields empty | 7+ error messages, `place_order` **not** called |

#### 2.4 `place_order()` → *(Rabia)* – mock `get_db()` (cursor, commit, rollback)
| ID | Scenario | Expected |
|----|----------|----------|
| CH-O1 | Happy path | returns `order_id`; `commit()` called; cart `DELETE` executed |
| CH-O2 | Cart empty on re-check | returns `None`, no commit |
| CH-O3 | Stock < quantity at re-check | returns `None`, flash "just went out of stock" |
| CH-O4 | `MySQLError` during insert | `rollback()` called, returns `None` |
| CH-O5 | Two items | 2 `order_items` inserts + 2 stock `UPDATE`s |
| CH-O6 | Item price copied into `order_items` | uses `item["price"]` |
| CH-O7 | New order status | `'Pending'` in SQL |

#### 2.5 `generate_order_code()` → *(either)*
Format `ORD-YYMMDD-XXXX` (regex `^ORD-\d{6}-[0-9A-F]{4}$`); if mocked `query_one` returns a row the first time → loops and returns a second code.
