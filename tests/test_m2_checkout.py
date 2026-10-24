import re
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from helpers import csv_cases

import app as shop

pytestmark = pytest.mark.m2


@pytest.mark.unit
@pytest.mark.boundary
class TestShippingCost:

    @pytest.mark.parametrize(
        "subtotal,expected", csv_cases("shipping_cost.csv", "subtotal", "expected")
    )
    def test_from_csv(self, subtotal, expected):
        assert str(shop.shipping_cost(Decimal(subtotal))) == expected


def make_cart_row(name="Phone", price="100", quantity=1, stock=10,
                  is_active=1, item_id=1):
    return {
        "item_id": item_id,
        "quantity": quantity,
        "product_id": item_id,
        "name": name,
        "slug": name.lower(),
        "price": price,
        "stock": stock,
        "image": "x.jpg",
        "is_active": is_active,
        "category_name": "Gadgets",
    }


def run_get_cart_items(rows):
    with patch.object(shop, "query_all", return_value=rows), \
         patch.object(shop, "session", {"user_id": 1}):
        return shop.get_cart_items()


@pytest.mark.unit
class TestGetCartItems:

    def test_empty_cart(self):
        assert run_get_cart_items([]) == []

    @pytest.mark.parametrize(
        "price,quantity,stock,is_active,line_total,out_of_stock",
        csv_cases(
            "cart_items.csv",
            "price",
            "quantity",
            "stock",
            "is_active",
            "expected_line_total",
            "expected_out_of_stock",
        ),
    )
    def test_from_csv(self, price, quantity, stock, is_active, line_total, out_of_stock):
        row = make_cart_row(
            price=price,
            quantity=int(quantity),
            stock=int(stock),
            is_active=int(is_active),
        )
        items = run_get_cart_items([row])
        assert len(items) == 1
        assert str(items[0]["line_total"]) == line_total
        assert str(items[0]["is_out_of_stock"]) == out_of_stock

    def test_multiple_items_keep_order(self):
        rows = [
            make_cart_row(name="Aaa", item_id=1),
            make_cart_row(name="Bbb", item_id=2),
            make_cart_row(name="Ccc", item_id=3),
        ]
        items = run_get_cart_items(rows)
        assert [i["name"] for i in items] == ["Aaa", "Bbb", "Ccc"]


USER = {
    "id": 1,
    "name": "Ali Khan",
    "email": "ali@example.com",
    "phone": "3001234567",
    "address": "House 12, Street 4",
    "is_admin": 0,
}

GOOD_ITEM = {
    "item_id": 1,
    "quantity": 1,
    "product_id": 1,
    "name": "Phone",
    "slug": "phone",
    "price": Decimal("100.00"),
    "stock": 5,
    "image": "x.jpg",
    "is_active": 1,
    "category_name": "Gadgets",
    "line_total": Decimal("100.00"),
    "is_out_of_stock": False,
}

BAD_ITEM = dict(GOOD_ITEM, name="Sold Out Phone", is_out_of_stock=True)

VALID_FORM = {
    "customer_name": "Ali Khan",
    "email": "ali@example.com",
    "phone": "3001234567",
    "address": "House 12, Street 4",
    "city": "Lahore",
    "state": "Punjab",
    "pincode": "540000",
    "payment_method": "Cash on Delivery",
}


def post_checkout(changes=None, cart=None, order_id=7, send_token=True):
    form = dict(VALID_FORM)
    form.update(changes or {})
    if send_token:
        form["csrf_token"] = "tok"

    cart = [GOOD_ITEM] if cart is None else cart

    with patch.object(shop, "get_current_user", return_value=USER), \
         patch.object(shop, "get_cart_items", return_value=cart), \
         patch.object(shop, "place_order", return_value=order_id) as fake_place, \
         patch.object(shop, "render_template", return_value="ok"), \
         patch.object(shop, "flash") as fake_flash:
        client = shop.app.test_client()
        with client.session_transaction() as sess:
            sess["_csrf_token"] = "tok"
        response = client.post("/checkout", data=form)

    messages = [call.args[0] for call in fake_flash.call_args_list]
    return response, fake_place, messages


@pytest.mark.route
class TestCheckoutRoute:

    @pytest.mark.smoke
    @pytest.mark.priority(1)
    def test_all_valid(self):
        response, fake_place, messages = post_checkout()
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/order/7/confirmation")
        fake_place.assert_called_once()

    def test_empty_cart(self):
        response, fake_place, messages = post_checkout(cart=[])
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/cart")
        assert any("empty" in m for m in messages)
        fake_place.assert_not_called()

    def test_out_of_stock_item(self):
        response, fake_place, messages = post_checkout(cart=[BAD_ITEM])
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/cart")
        assert any("update your cart first" in m for m in messages)
        fake_place.assert_not_called()

    def test_place_order_fails(self):
        response, fake_place, messages = post_checkout(order_id=None)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/cart")
        assert any("could not place" in m for m in messages)

    def test_get_shows_form(self):
        with patch.object(shop, "get_current_user", return_value=USER), \
             patch.object(shop, "get_cart_items", return_value=[GOOD_ITEM]), \
             patch.object(shop, "place_order") as fake_place, \
             patch.object(shop, "render_template", return_value="ok"):
            response = shop.app.test_client().get("/checkout")
        assert response.status_code == 200
        fake_place.assert_not_called()


@pytest.mark.route
@pytest.mark.boundary
class TestCheckoutValidation:

    @pytest.mark.parametrize(
        "field,value,should_pass,message",
        csv_cases(
            "checkout_fields.csv", "field", "value", "should_pass", "expected_message"
        ),
    )
    def test_field_rules(self, field, value, should_pass, message):
        response, fake_place, messages = post_checkout({field: value})

        if should_pass == "yes":
            assert response.status_code == 302
            fake_place.assert_called_once()
        else:
            assert response.status_code == 200
            fake_place.assert_not_called()
            assert any(message in m for m in messages)

    def test_all_fields_empty(self):
        blank = {field: "" for field in VALID_FORM}
        response, fake_place, messages = post_checkout(blank)
        assert response.status_code == 200
        assert len(messages) >= 7
        fake_place.assert_not_called()


@pytest.mark.route
@pytest.mark.security
class TestCheckoutSecurity:

    def test_missing_csrf_token(self):
        response, fake_place, messages = post_checkout(send_token=False)
        assert response.status_code == 400
        fake_place.assert_not_called()


def fresh_item(item_id=1, name="Phone", price="19.99", stock=5, quantity=2):
    return {
        "id": item_id,
        "name": name,
        "price": Decimal(price),
        "stock": stock,
        "quantity": quantity,
    }


def run_place_order(fresh_items, execute_effects=None):
    cursor = MagicMock()
    cursor.fetchall.return_value = fresh_items
    cursor.lastrowid = 55
    if execute_effects is not None:
        cursor.execute.side_effect = execute_effects

    database = MagicMock()
    database.cursor.return_value = cursor

    with patch.object(shop, "get_db", return_value=database), \
         patch.object(shop, "session", {"user_id": 1}), \
         patch.object(shop, "generate_order_code", return_value="ORD-TEST"), \
         patch.object(shop, "flash") as fake_flash:
        result = shop.place_order(VALID_FORM, [], Decimal("100.00"))

    return result, database, cursor, fake_flash


def sql_list(cursor):
    return [call.args[0] for call in cursor.execute.call_args_list]


@pytest.mark.unit
class TestPlaceOrder:

    @pytest.mark.smoke
    @pytest.mark.priority(1)
    def test_happy_path(self):
        result, database, cursor, _ = run_place_order([fresh_item()])
        assert result == 55
        database.commit.assert_called_once()
        database.rollback.assert_not_called()
        assert any("DELETE FROM cart_items" in sql for sql in sql_list(cursor))

    def test_empty_cart(self):
        result, database, cursor, _ = run_place_order([])
        assert result is None
        database.commit.assert_not_called()

    def test_stock_too_low_flashes_message(self):
        result, database, cursor, fake_flash = run_place_order(
            [fresh_item(stock=1, quantity=2)]
        )
        messages = [call.args[0] for call in fake_flash.call_args_list]
        assert result is None
        database.commit.assert_not_called()
        assert any("just went out of stock" in m for m in messages)

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "stock,quantity,expected",
        csv_cases("place_order_stock.csv", "stock", "quantity", "expected"),
    )
    def test_stock_boundary_from_csv(self, stock, quantity, expected):
        item = fresh_item(stock=int(stock), quantity=int(quantity))
        result, database, cursor, _ = run_place_order([item])

        if expected == "ok":
            assert result == 55
            database.commit.assert_called_once()
        else:
            assert result is None
            database.commit.assert_not_called()

    def test_mysql_error_rolls_back(self):
        result, database, cursor, _ = run_place_order(
            [fresh_item()],
            execute_effects=[None, shop.MySQLError("boom")],
        )
        assert result is None
        database.rollback.assert_called_once()
        database.commit.assert_not_called()

    def test_two_items(self):
        items = [
            fresh_item(item_id=1, name="Phone"),
            fresh_item(item_id=2, name="Case"),
        ]
        result, database, cursor, _ = run_place_order(items)
        sqls = sql_list(cursor)
        assert result == 55
        assert sum("INSERT INTO order_items" in s for s in sqls) == 2
        assert sum("UPDATE products SET stock" in s for s in sqls) == 2

    def test_price_copied_into_order_items(self):
        result, database, cursor, _ = run_place_order([fresh_item(price="19.99")])
        insert_calls = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO order_items" in call.args[0]
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0].args[1]
        assert params[0] == 55
        assert params[3] == Decimal("19.99")
        assert params[4] == 2

    def test_stock_reduced_by_quantity(self):
        result, database, cursor, _ = run_place_order(
            [fresh_item(item_id=9, quantity=2)]
        )
        update_calls = [
            call for call in cursor.execute.call_args_list
            if "UPDATE products SET stock" in call.args[0]
        ]
        assert update_calls[0].args[1] == (2, 9)

    def test_new_order_status_pending(self):
        result, database, cursor, _ = run_place_order([fresh_item()])
        order_sql = [s for s in sql_list(cursor) if "INSERT INTO orders" in s]
        assert len(order_sql) == 1
        assert "'Pending'" in order_sql[0]


ORDER_CODE_PATTERN = re.compile(r"^ORD-\d{6}-[0-9A-F]{4}$")


@pytest.mark.unit
class TestGenerateOrderCode:

    def test_format(self):
        with patch.object(shop, "query_one", return_value=None):
            code = shop.generate_order_code()
        assert ORDER_CODE_PATTERN.match(code)

    def test_has_todays_date(self):
        with patch.object(shop, "query_one", return_value=None):
            code = shop.generate_order_code()
        assert code.split("-")[1] == datetime.now().strftime("%y%m%d")

    def test_retries_when_taken(self):
        with patch.object(shop, "query_one", side_effect=[{"id": 1}, None]) as fake_query, \
             patch.object(shop.secrets, "token_hex", side_effect=["aaaa", "bbbb"]):
            code = shop.generate_order_code()
        assert fake_query.call_count == 2
        assert code.endswith("-BBBB")
        assert ORDER_CODE_PATTERN.match(code)
