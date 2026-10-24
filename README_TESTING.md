# ShopSphere – Test Configuration and How to Run (Task 4)

## 1. Setup

Copy the contents of this folder into the project root (the folder that contains `app.py`).

```
project/
├── app.py
├── config.py
├── pytest.ini            <- configuration (markers, options)
├── run_tests.py          <- one-command runner for every suite
├── requirements-test.txt
└── tests/
    ├── conftest.py       <- run order + parallel grouping
    ├── helpers.py        <- CSV loader used for data-driven tests
    ├── test_m1_auth.py
    ├── test_m2_checkout.py
    ├── test_m3_simple.py
    └── data/*.csv        <- test data (13 files)
```

Install the test tools once:

```
pip install -r requirements-test.txt
```

## 2. Test groups (suites)

Every test belongs to one **module group** and one **type group**, set with pytest markers.

| Marker | Meaning | Where |
|--------|---------|-------|
| `m1` | Module 1 – Authentication | `test_m1_auth.py` |
| `m2` | Module 2 – Checkout and orders | `test_m2_checkout.py` |
| `m3` | Module 3 – Utilities and public pages | `test_m3_simple.py` |
| `unit` | Single function, no HTTP request | classes `TestIsValidEmail`, `TestShippingCost`, ... |
| `route` | Flask route through the test client | classes `TestRegister`, `TestCheckoutRoute`, ... |
| `security` | CSRF, open redirect, access control, hashing | classes `...Security`, `TestAccessControl` |
| `boundary` | Boundary value analysis cases | email, password, shipping, stock, pagination |
| `smoke` | Quick sanity check, runs first in each module | one or two per module |

Run a group with `-m`, for example `pytest -m security`.

## 3. Commands

| Goal | Command |
|------|---------|
| Everything, in order | `pytest` or `python run_tests.py` |
| One module | `python run_tests.py m1` (also `m2`, `m3`) |
| One type | `python run_tests.py unit` / `route` / `security` / `boundary` |
| Quick check | `python run_tests.py smoke` |
| Several suites | `python run_tests.py m1 m2` or `pytest -m "m1 or security"` |
| In parallel | `python run_tests.py --parallel` or `pytest -n auto --dist loadgroup` |
| Parallel, one suite | `python run_tests.py m2 --parallel` |
| Stop at first failure | `python run_tests.py -- -x` |
| One test by CSV id | `pytest -k "AU-E3"` or `pytest -k "CH-S5"` |
| List tests without running | `pytest --collect-only -q` |

## 4. Parallel execution

Parallel runs use **pytest-xdist**. `-n auto` starts one worker per CPU core and
`--dist loadgroup` keeps every module on a single worker. `conftest.py` adds the
`xdist_group` marker to each test automatically (group name = `m1`, `m2` or `m3`), so
the order inside a module is still kept when running in parallel. All tests use mocks and
share no database, so they are safe to run at the same time.

## 5. Data-driven tests (parameterization)

Test data lives in `tests/data/*.csv`. `helpers.csv_cases()` turns each CSV row into its own
test case, named by the `id` column:

```python
@pytest.mark.parametrize(
    "subtotal,expected", csv_cases("shipping_cost.csv", "subtotal", "expected")
)
def test_from_csv(self, subtotal, expected):
    assert str(shop.shipping_cost(Decimal(subtotal))) == expected
```

Result: `test_from_csv[CH-S5]`, `test_from_csv[CH-S6]`, ... Each row passes or fails on its own.
Values that cannot be written in CSV (`None`, 72-character strings) use inline
`@pytest.mark.parametrize` lists with ids such as `AU-P3`, `AU-P4`.

To add a test case, add one row to the CSV. No Python change is needed.

| CSV file | Tests |
|----------|-------|
| `is_valid_email.csv`, `password_problem.csv`, `safe_next_url.csv` | M1 unit |
| `register_fields.csv`, `login_cases.csv` | M1 routes |
| `shipping_cost.csv`, `cart_items.csv`, `place_order_stock.csv` | M2 unit |
| `checkout_fields.csv` | M2 route validation |
| `to_money.csv`, `to_int.csv`, `clean.csv`, `slugify.csv` | M3 unit |

## 6. Execution order

`tests/conftest.py` sorts the tests before they run, using this key:

1. **Module order** `m3 -> m1 -> m2`: helpers first, then authentication, then checkout, which builds on both.
2. **Priority** (`@pytest.mark.priority(n)`, default 5, lower runs first): smoke tests use `1`, so they run first inside their module.
3. **Type order** `unit -> route -> security`.
4. Anything left keeps the order of the file.

To change the order, edit the two lists at the top of `conftest.py`:

```python
MODULE_ORDER = ["m3", "m1", "m2"]
LEVEL_ORDER = ["unit", "route", "security"]
```

To see the order: `pytest --collect-only -q`.

## 7. Known defects recorded as `xfail`

| Test | Defect |
|------|--------|
| `test_m1_auth.py::TestSafeNextUrl::test_backslash_prefix` (AU-N8) | `safe_next_url("/\\evil.com")` is returned unchanged, so it is an open redirect. |
| `test_m3_simple.py::TestToMoney::test_nan` | `to_money("NaN")` raises `InvalidOperation` instead of returning `None`, so `/products?min_price=NaN` would crash. |

They show as `xfailed`, not as failures. When a defect is fixed they show as `XPASS`; remove the `xfail` marker then.
