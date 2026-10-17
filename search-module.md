# M3 – Product Search, Filter & Details

#### 3.1 `to_money(value)` → *(Noor)*
**Technique:** BVA on 0 and 99,999,999.99; ECP on text.

| ID | Input | Expected |
|----|-------|----------|
| PS-M1 | `"0"` | `Decimal("0.00")` |
| PS-M2 | `"-0.01"` | `None` |
| PS-M3 | `"99999999.99"` | `Decimal("99999999.99")` |
| PS-M4 | `"100000000"` | `None` |
| PS-M5 | `"abc"`, `""`, `None` | `None` |
| PS-M6 | `"1.015"` | `1.02` (rounding) |
| PS-M7 | `"1e2"` | `100.00` |
| PS-M8 | `"Infinity"` | `None` |
| PS-M9 | `"NaN"` | **Expected `None`, actually raises `decimal.InvalidOperation`** → real bug: `/products?min_price=NaN` would give a 500. Write the test for correct behaviour and record the defect. |

#### 3.2 `to_int` and `clean` → *(Noor)*
| ID | Function | Input | Expected |
|----|----------|-------|----------|
| PS-I1 | `to_int` | `"5"`, `" 7 "` | 5, 7 |
| PS-I2 | `to_int` | `"5.5"`, `"abc"`, `None`, `""` | `None` (default) |
| PS-I3 | `to_int` | `"-3"` | -3 |
| PS-I4 | `to_int` | `"abc"`, default=1 | 1 |
| PS-C1 | `clean` | `"  hi  "` | `"hi"` |
| PS-C2 | `clean` | `None` | `""` |
| PS-C3 | `clean` | `"abcdef"`, max 3 | `"abc"` |
| PS-C4 | `clean` | length = max / max+1 | unchanged / truncated |

#### 3.3 `slugify` and `make_unique_slug` → *(Rabia)*
| ID | Input | Expected |
|----|-------|----------|
| PS-S1 | `Nova X1 Smartphone` | `nova-x1-smartphone` |
| PS-S2 | `"  A  B "` | `a-b` |
| PS-S3 | `O'Brien` | `obrien` |
| PS-S4 | Urdu / emoji only (`اردو`) | `item` (fallback) |
| PS-S5 | `""` / `None` | `item` |
| PS-S6 | `Café` | `cafe` |
| PS-S7 | `<b>x</b>` | `bxb` (tags not stripped – note) |
| PS-U1 | `make_unique_slug`, slug free | plain slug |
| PS-U2 | slug taken once | `slug-2` |
| PS-U3 | slug taken twice | `slug-3` |
| PS-U4 | `ignore_id` = own id | keeps own slug when editing |

> Note for report: two different Urdu names both become `item` – ties in with your manual EG-3 finding.

#### 3.4 `products()` route (search / filter / sort / page) → *(Noor)* – mock `query_all`, `query_one`
**Technique:** ECP on each filter, BVA on page and price, pairwise for combinations.

| ID | Scenario | Expected |
|----|----------|----------|
| PS-P1 | No params | default sort `newest`, page 1, 200 OK |
| PS-P2 | `q=cup` | SQL has `LIKE`; params `%cup%` twice |
| PS-P3 | `q` of 100 / 101 chars | trimmed to 100 |
| PS-P4 | `q` = `' OR 1=1 --` | passed as parameter, no crash |
| PS-P5 | `category=abc` | 200, empty result |
| PS-P6 | `min_price=100&max_price=500` | both conditions added |
| PS-P7 | `min_price=500&max_price=100` (min > max) | 200, empty result (note behaviour) |
| PS-P8 | `min_price=-1` / `abc` | ignored |
| PS-P9 | `sort=price_low` / `price_high` / `name` | matching `ORDER BY` |
| PS-P10 | `sort=DROP TABLE` | falls back to `newest` |
| PS-P11 | `page=0`, `-1`, `abc` | page 1 |
| PS-P12 | `page=999` (> last) | clamped to last page |
| PS-P13 | 9 items → 1 page; 10 items → 2 pages (BVA on per-page = 9) | `total_pages` 1 / 2 |

#### 3.5 `product_details(slug)` → *(Rabia)*
| ID | Scenario | Expected |
|----|----------|----------|
| PS-D1 | Existing slug | 200, product name in page |
| PS-D2 | Unknown slug | 404 |
| PS-D3 | Archived product (`is_active=0`) | 404 (query filters it) |
| PS-D4 | Related products | at most 4, excludes current product |
| PS-D5 | Product with no related items | 200, empty list |
| PS-D6 | Slug with odd characters `%00`, very long | 404, no 500 |
