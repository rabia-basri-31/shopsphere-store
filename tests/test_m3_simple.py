

import csv
import sys
import os
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import app as shop


DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_csv(name):
    """Read a CSV file from tests/data/ and return its rows."""
    file_path = os.path.join(DATA, name)

    with open(file_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))



def test_to_money_from_csv():
    for row in read_csv("to_money.csv"):
        result = shop.to_money(row["input"])
        assert str(result) == row["expected"]


def test_to_money_none():
    assert shop.to_money(None) is None


def test_to_money_empty():
    assert shop.to_money("") is None


def test_to_money_nan():
    assert shop.to_money("NaN") is None



def test_to_int_from_csv():
    for row in read_csv("to_int.csv"):
        assert str(shop.to_int(row["input"])) == row["expected"]


def test_to_int_spaces():
    assert shop.to_int(" 7 ") == 7


def test_to_int_default():
    assert shop.to_int("abc", 1) == 1


def test_to_int_none():
    assert shop.to_int(None) is None




def test_clean_from_csv():
    for row in read_csv("clean.csv"):
        assert shop.clean(
            row["input"], int(row["max_length"])
        ) == row["expected"]


def test_clean_spaces():
    assert shop.clean("  hi  ") == "hi"


def test_clean_none():
    assert shop.clean(None) == ""




def test_slugify_from_csv():
    for row in read_csv("slugify.csv"):
        assert shop.slugify(row["input"]) == row["expected"]


def test_slugify_extra_spaces():
    assert shop.slugify("  A  B ") == "a-b"


def test_slugify_empty():
    assert shop.slugify("") == "item"


def test_slugify_none():
    assert shop.slugify(None) == "item"



def test_unique_slug_free():
    with patch.object(shop, "query_one", side_effect=[None]):
        assert shop.make_unique_slug("Red Cup") == "red-cup"


def test_unique_slug_taken_once():
    with patch.object(shop, "query_one", side_effect=[{"id": 1}, None]):
        assert shop.make_unique_slug("Red Cup") == "red-cup-2"


def test_unique_slug_taken_twice():
    with patch.object(
        shop, "query_one",
        side_effect=[{"id": 1}, {"id": 2}, None]
    ):
        assert shop.make_unique_slug("Red Cup") == "red-cup-3"


def test_unique_slug_own_id():
    with patch.object(shop, "query_one", side_effect=[None]):
        assert shop.make_unique_slug(
            "Red Cup", ignore_id=1
        ) == "red-cup"


def open_products(url, total=0):
    """Open a URL with a fake database."""
    with patch.object(shop, "query_one", return_value={"total": total}), \
         patch.object(shop, "query_all", return_value=[]), \
         patch.object(
             shop, "render_template", return_value="ok"
         ) as fake_page:
        response = shop.app.test_client().get(url)

    return response, fake_page.call_args.kwargs


def test_products_default():
    response, data = open_products("/products")
    assert response.status_code == 200
    assert data["sort_option"] == "newest"
    assert data["page"] == 1


def test_products_bad_sort():
    response, data = open_products("/products?sort=DROP TABLE")
    assert response.status_code == 200


def test_products_page_zero():
    response, data = open_products("/products?page=0", total=30)
    assert data["page"] == 1


def test_products_page_too_big():
    response, data = open_products("/products?page=999", total=30)
    assert data["page"] == data["total_pages"]


def test_products_9_items_one_page():
    response, data = open_products("/products", total=9)
    assert data["total_pages"] == 1


def test_products_10_items_two_pages():
    response, data = open_products("/products", total=10)
    assert data["total_pages"] == 2


def test_products_sql_injection_text():
    response, data = open_products("/products?q=' OR 1=1 --")
    assert response.status_code == 200


def open_details(slug, product):
    with patch.object(shop, "query_one", return_value=product), \
         patch.object(shop, "query_all", return_value=[]), \
         patch.object(shop, "render_template", return_value="ok"):
        return shop.app.test_client().get("/product/" + slug)


def test_details_found():
    product = {"id": 1, "name": "Phone", "category_id": 2}
    assert open_details("phone", product).status_code == 200


def test_details_not_found():
    assert open_details("no-such-item", None).status_code == 404


def test_details_long_slug():
    assert open_details("a" * 2000, None).status_code == 404
