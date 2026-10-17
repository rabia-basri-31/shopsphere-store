# ShopSphere – Unit Test Automation (Assignment 3)

**Course:** Software Quality Engineering (SQE), 5-A
**Group:** Noor Ul Ain (F243094) · Rabia Basri (F243105)
**Project under test:** [ShopSphere](https://github.com/Naveen796/ecommerce-web-app) (Flask + MySQL)
**Framework:** pytest, pytest-xdist, pytest-ordering, pytest-html

## Documentation

| Task | File |
|------|------|
| Task 1 – Environment setup + video | [docs/SETUP.md](docs/SETUP.md) |
| Task 2 – Modules & work split | [docs/test-design/00-modules-and-split.md](docs/test-design/00-modules-and-split.md) |
| Task 2 – Rules taken from the code | [docs/test-design/01-rules-from-code.md](docs/test-design/01-rules-from-code.md) |
| Task 2 – M1 User Authentication (ECP/BVA) | [docs/test-design/02-auth-module.md](docs/test-design/02-auth-module.md) |
| Task 2 – M2 Checkout (ECP/BVA) | [docs/test-design/03-checkout-module.md](docs/test-design/03-checkout-module.md) |
| Task 2 – M3 Product Search/Filter/Details | [docs/test-design/04-search-product-module.md](docs/test-design/04-search-product-module.md) |
| Task 3 – CSV data-driven tests | [docs/TASK3-csv-data-driven.md](docs/TASK3-csv-data-driven.md) |
| Task 4 – Config, groups, order, parallel | [docs/TASK4-execution-config.md](docs/TASK4-execution-config.md) |
| Defects found | [docs/defects-found.md](docs/defects-found.md) |
| Git workflow | [docs/git-workflow.md](docs/git-workflow.md) |
| Excel test cases | `docs/Test_Cases.xlsx` (add later) |
| Setup video | `docs/setup-video.mp4` (add later) |

## How to run the tests

```bash
pip install -r requirements.txt
pip install pytest pytest-xdist pytest-ordering pytest-html
pytest                    # full suite
pytest -m auth            # one group
pytest -n auto            # parallel
```

## Repository structure

```
.
├── README.md
├── pytest.ini
├── docs/
│   ├── SETUP.md
│   ├── TASK3-csv-data-driven.md
│   ├── TASK4-execution-config.md
│   ├── defects-found.md
│   ├── git-workflow.md
│   └── test-design/
│       ├── 00-modules-and-split.md
│       ├── 01-rules-from-code.md
│       ├── 02-auth-module.md
│       ├── 03-checkout-module.md
│       └── 04-search-product-module.md
└── tests/
    ├── conftest.py
    ├── utils.py
    ├── data/
    ├── auth/
    ├── checkout/
    └── search/
```
