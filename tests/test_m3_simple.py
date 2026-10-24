from unittest.mock import patch

import pytest

from helpers import csv_cases

import app as shop

pytestmark = pytest.mark.m3


@pytest.mark.unit
@pytest.mark.boundary
class TestToMoney:

    @pytest.mark.parametrize(
        "value,expected", csv_cases("to_money.csv", "input", "expected")
    )
    def test_from_csv(self, value, expected):
        assert str(shop.to_money(value)) == expected

    @pytest.mark.parametrize(
        "value", [None, ""], ids=["none", "empty"]
    )
    def test_missing_input(self, value):
        assert shop.to_money(value) is None

    @pytest.mark.xfail(
        reason="defect: to_money('NaN') raises InvalidOperation instead of returning None"
    )
    def test_nan(self):
        assert shop.to_money("NaN") is None


@pytest.mark.unit
@pytest.mark.boundary
class TestToInt:

    @pytest.mark.parametrize(
        "value,expected", csv_cases("to_int.csv", "input", "expected")
    )
    def test_from_csv(self, value, expected):
        assert str(shop.to_int(value)) == expected

    def test_none(self):
        assert shop.to_int(None) is None

    @pytest.mark.parametrize(
        "value,default,expected",
        [("abc", 1, 1), (None, 5, 5), ("", 9, 9), ("12", 9, 12)],
    )
    def test_default_value(self, value, default, expected):
        assert shop.to_int(value, default) == expected


@pytest.mark.unit
class TestClean:

    @pytest.mark.parametrize(
        "value,max_length,expected",
        csv_cases("clean.csv", "input", "max_length", "expected"),
    )
    def test_from_csv(self, value, max_length, expected):
        assert shop.clean(value, int(max_length)) == expected

    def test_none(self):
        assert shop.clean(None) == ""

    def test_spaces_without_limit(self):
        assert shop.clean("  hi  ") == "hi"


@pytest.mark.unit
class TestSlugify:

    @pytest.mark.parametrize(
        "value,expected", csv_cases("slugify.csv", "input", "expected")
    )
    def test_from_csv(self, value, expected):
        assert shop.slugify(value) == expected

    @pytest.mark.parametrize("value", ["", None], ids=["empty", "none"])
    def test_empty_gives_item(self, value):
        assert shop.slugify(value) == "item"


@pytest.mark.unit
class TestMakeUniqueSlug:

    @pytest.mark.parametrize(
        "lookups,expected",
        [
            pytest.param([None], "red-cup", id="free"),
            pytest.param([{"id": 1}, None], "red-cup-2", id="taken-once"),
            pytest.param([{"id": 1}, {"id": 2}, None], "red-cup-3", id="taken-twice"),
        ],
    )
    def test_suffix_added_until_free(self, lookups, expected):
        with patch.object(shop, "query_one", side_effect=lookups):
            assert shop.make_unique_slug("Red Cup") == expected

    def test_ignores_own_id(self):
        with patch.object(shop, "query_one", side_effect=[None]):
            assert shop.make_unique_slug("Red Cup", ignore_id=1) == "red-cup"


def open_products(url, total=0):
    with patch.object(shop, "query_one", return_value={"total": total}), \
         patch.object(shop, "query_all", return_value=[]), \
         patch.object(shop, "render_template", return_value="ok") as fake_page:
        response = shop.app.test_client().get(url)

    return response, fake_page.call_args.kwargs


def open_details(slug, product):
    with patch.object(shop, "query_one", return_value=product), \
         patch.object(shop, "query_all", return_value=[]), \
         patch.object(shop, "render_template", return_value="ok"):
        return shop.app.test_client().get("/product/" + slug)


@pytest.mark.route
class TestProductsPage:

    @pytest.mark.smoke
    @pytest.mark.priority(1)
    def test_default(self):
        response, data = open_products("/products")
        assert response.status_code == 200
        assert data["sort_option"] == "newest"
        assert data["page"] == 1

    def test_bad_sort_value(self):
        response, data = open_products("/products?sort=DROP TABLE")
        assert response.status_code == 200

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "total,expected_pages",
        [(0, 1), (9, 1), (10, 2), (18, 2), (19, 3)],
    )
    def test_page_count(self, total, expected_pages):
        response, data = open_products("/products", total=total)
        assert data["total_pages"] == expected_pages

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "url",
        ["/products?page=0", "/products?page=-5", "/products?page=abc"],
        ids=["zero", "negative", "text"],
    )
    def test_bad_page_falls_back_to_first(self, url):
        response, data = open_products(url, total=30)
        assert data["page"] == 1

    def test_page_too_big_goes_to_last(self):
        response, data = open_products("/products?page=999", total=30)
        assert data["page"] == data["total_pages"]


@pytest.mark.route
@pytest.mark.security
class TestProductsSecurity:

    def test_sql_injection_text_in_search(self):
        response, data = open_products("/products?q=' OR 1=1 --")
        assert response.status_code == 200


@pytest.mark.route
class TestProductDetails:

    @pytest.mark.smoke
    @pytest.mark.priority(1)
    def test_found(self):
        product = {"id": 1, "name": "Phone", "category_id": 2}
        assert open_details("phone", product).status_code == 200

    @pytest.mark.parametrize(
        "slug", ["no-such-item", "a" * 2000], ids=["unknown", "very-long"]
    )
    def test_not_found(self, slug):
        assert open_details(slug, None).status_code == 404
