"""
M2 - Checkout & Order Placement  (tests for app.py)

Put this file in  tests/
Put the CSV files in  tests/data/
    shipping_cost.csv, cart_items.csv, checkout_fields.csv, place_order_stock.csv

Run with:   pytest tests/test_m2_checkout.py -v
"""

import csv
import os
import re
import sys
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import app as shop


DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_csv(name):
    """Read a CSV file from tests/data/ and return its rows."""
    file_path = os.path.join(DATA, name)

    with open(file_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ======================================================================
#  2.1  shipping_cost(subtotal)      - BVA around 0 and 999.00
# ======================================================================

def test_shipping_cost_from_csv():
    for row in read_csv("shipping_cost.csv"):
        result = shop.shipping_cost(Decimal(row["subtotal"]))
        assert str(result) == row["expected"], row["id"]


def test_shipping_cost_negative():                      # CH-S1
    assert shop.shipping_cost(Decimal("-5")) == Decimal("0.00")


def test_shipping_cost_zero():                          # CH-S2
    assert shop.shipping_cost(Decimal("0")) == Decimal("0.00")


def test_shipping_cost_just_above_zero():               # CH-S3
    assert shop.shipping_cost(Decimal("0.01")) == Decimal("79.00")


def test_shipping_cost_just_below_limit():              # CH-S4
    assert shop.shipping_cost(Decimal("998.99")) == Decimal("79.00")


def test_shipping_cost_exact_limit():                   # CH-S5
    assert shop.shipping_cost(Decimal("999.00")) == Decimal("0.00")


def test_shipping_cost_just_above_limit():             # CH-S6
    assert shop.shipping_cost(Decimal("999.01")) == Decimal("0.00")


def test_shipping_cost_large():                         # CH-S7
    assert shop.shipping_cost(Decimal("5000")) == Decimal("0.00")


def test_shipping_cost_typical():                       # CH-S8
    assert shop.shipping_cost(Decimal("500")) == Decimal("79.00")


# ======================================================================
#  2.2  get_cart_items()     - mock query_all and session
# ======================================================================

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


def test_cart_items_empty():                            # CH-C1
    assert run_get_cart_items([]) == []


def test_cart_items_from_csv():                         # CH-C2..C8
    for row in read_csv("cart_items.csv"):
        cart_row = make_cart_row(
            price=row["price"],
            quantity=int(row["quantity"]),
            stock=int(row["stock"]),
            is_active=int(row["is_active"]),
        )
        items = run_get_cart_items([cart_row])
        assert len(items) == 1, row["id"]
        assert items[0]["line_total"] == Decimal(row["expected_line_total"]), row["id"]
        assert str(items[0]["is_out_of_stock"]) == row["expected_out_of_stock"], row["id"]


def test_cart_items_line_total():                       # CH-C2
    items = run_get_cart_items([make_cart_row(price="100", quantity=3)])
    assert items[0]["line_total"] == Decimal("300")


def test_cart_items_qty_equals_stock():                 # CH-C3
    items = run_get_cart_items([make_cart_row(quantity=5, stock=5)])
    assert items[0]["is_out_of_stock"] is False


def test_cart_items_qty_above_stock():                  # CH-C4
    items = run_get_cart_items([make_cart_row(quantity=6, stock=5)])
    assert items[0]["is_out_of_stock"] is True


def test_cart_items_zero_stock():                       # CH-C5
    items = run_get_cart_items([make_cart_row(quantity=1, stock=0)])
    assert items[0]["is_out_of_stock"] is True


def test_cart_items_archived_product():                 # CH-C6
    items = run_get_cart_items([make_cart_row(is_active=0)])
    assert items[0]["is_out_of_stock"] is True


def test_cart_items_multiple_keep_order():              # CH-C7
    rows = [
        make_cart_row(name="Aaa", item_id=1),
        make_cart_row(name="Bbb", item_id=2),
        make_cart_row(name="Ccc", item_id=3),
    ]
    items = run_get_cart_items(rows)
    assert len(items) == 3
    assert [i["name"] for i in items] == ["Aaa", "Bbb", "Ccc"]


def test_cart_items_decimal_no_float_error():           # CH-C8
    items = run_get_cart_items([make_cart_row(price="19.99", quantity=3)])
    assert items[0]["line_total"] == Decimal("59.97")
    assert str(items[0]["line_total"]) == "59.97"


# ======================================================================
#  2.3  checkout() route validation
#       Mock: get_current_user, get_cart_items, place_order,
#             render_template, flash
# ======================================================================

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
    """
    POST /checkout with a fake database.
    Returns (response, fake_place_order, flashed_messages).
    """
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


def test_checkout_empty_cart():                         # CH-V1
    response, fake_place, messages = post_checkout(cart=[])
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/cart")
    assert any("empty" in m for m in messages)
    fake_place.assert_not_called()


def test_checkout_out_of_stock_item():                  # CH-V2
    response, fake_place, messages = post_checkout(cart=[BAD_ITEM])
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/cart")
    assert any("update your cart first" in m for m in messages)
    fake_place.assert_not_called()


def test_checkout_all_valid():                          # CH-V3
    response, fake_place, messages = post_checkout()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/order/7/confirmation")
    fake_place.assert_called_once()


def test_checkout_place_order_fails():
    response, fake_place, messages = post_checkout(order_id=None)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/cart")
    assert any("could not place" in m for m in messages)


def test_checkout_fields_from_csv():                    # CH-V4..V9
    for row in read_csv("checkout_fields.csv"):
        response, fake_place, messages = post_checkout({row["field"]: row["value"]})

        if row["should_pass"] == "yes":
            assert response.status_code == 302, row["id"]
            fake_place.assert_called_once()
        else:
            assert response.status_code == 200, row["id"]
            fake_place.assert_not_called()
            assert any(row["expected_message"] in m for m in messages), row["id"]


def test_checkout_all_fields_empty():                   # CH-V10
    blank = {field: "" for field in VALID_FORM}
    response, fake_place, messages = post_checkout(blank)
    assert response.status_code == 200
    assert len(messages) >= 7
    fake_place.assert_not_called()


def test_checkout_get_shows_form():
    with patch.object(shop, "get_current_user", return_value=USER), \
         patch.object(shop, "get_cart_items", return_value=[GOOD_ITEM]), \
         patch.object(shop, "place_order") as fake_place, \
         patch.object(shop, "render_template", return_value="ok"):
        response = shop.app.test_client().get("/checkout")
    assert response.status_code == 200
    fake_place.assert_not_called()


def test_checkout_missing_csrf_token():
    response, fake_place, messages = post_checkout(send_token=False)
    assert response.status_code == 400
    fake_place.assert_not_called()


# ======================================================================
#  2.4  place_order()      - mock get_db() (cursor, commit, rollback)
# ======================================================================

def fresh_item(item_id=1, name="Phone", price="19.99", stock=5, quantity=2):
    return {
        "id": item_id,
        "name": name,
        "price": Decimal(price),
        "stock": stock,
        "quantity": quantity,
    }


def run_place_order(fresh_items, execute_effects=None):
    """
    Call place_order() with a fake database.
    Returns (result, database, cursor, fake_flash).
    """
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
    """Every SQL string that was passed to cursor.execute()."""
    return [call.args[0] for call in cursor.execute.call_args_list]



def test_place_order_happy_path():                      # CH-O1
    result, database, cursor, _ = run_place_order([fresh_item()])
    assert result == 55
    database.commit.assert_called_once()
    database.rollback.assert_not_called()
    assert any("DELETE FROM cart_items" in sql for sql in sql_list(cursor))




def test_place_order_empty_cart():                      # CH-O2
    result, database, cursor, _ = run_place_order([])
    assert result is None
    database.commit.assert_not_called()




def test_place_order_stock_too_low():                   # CH-O3
    result, database, cursor, fake_flash = run_place_order(
        [fresh_item(stock=1, quantity=2)]
    )
    assert result is None
    database.commit.assert_not_called()
    messages = [call.args[0] for call in fake_flash.call_args_list]
    assert any("just went out of stock" in m for m in messages)




def test_place_order_stock_from_csv():                  # CH-O3 (BVA)
    for row in read_csv("place_order_stock.csv"):
        item = fresh_item(stock=int(row["stock"]), quantity=int(row["quantity"]))
        result, database, cursor, _ = run_place_order([item])
        if row["expected"] == "ok":
            assert result == 55, row["id"]
            database.commit.assert_called_once()
        else:
            assert result is None, row["id"]
            database.commit.assert_not_called()




def test_place_order_mysql_error_rolls_back():          # CH-O4
    result, database, cursor, _ = run_place_order(
        [fresh_item()],
        execute_effects=[None, shop.MySQLError("boom")],
    )
    assert result is None
    database.rollback.assert_called_once()
    database.commit.assert_not_called()




def test_place_order_two_items():                       # CH-O5
    items = [fresh_item(item_id=1, name="Phone"), fresh_item(item_id=2, name="Case")]
    result, database, cursor, _ = run_place_order(items)
    sqls = sql_list(cursor)
    assert result == 55
    assert sum("INSERT INTO order_items" in s for s in sqls) == 2
    assert sum("UPDATE products SET stock" in s for s in sqls) == 2




def test_place_order_price_copied():                    # CH-O6
    result, database, cursor, _ = run_place_order([fresh_item(price="19.99")])
    insert_calls = [
        call for call in cursor.execute.call_args_list
        if "INSERT INTO order_items" in call.args[0]
    ]
    assert len(insert_calls) == 1
    params = insert_calls[0].args[1]
    assert params[0] == 55                    # order_id
    assert params[3] == Decimal("19.99")      # price copied from the item
    assert params[4] == 2                     # quantity




def test_place_order_stock_reduced_by_quantity():
    result, database, cursor, _ = run_place_order([fresh_item(item_id=9, quantity=2)])
    update_calls = [
        call for call in cursor.execute.call_args_list
        if "UPDATE products SET stock" in call.args[0]
    ]
    assert update_calls[0].args[1] == (2, 9)




def test_place_order_status_pending():                  # CH-O7
    result, database, cursor, _ = run_place_order([fresh_item()])
    order_sql = [s for s in sql_list(cursor) if "INSERT INTO orders" in s]
    assert len(order_sql) == 1
    assert "'Pending'" in order_sql[0]




# ======================================================================
#  2.5  generate_order_code()
# ======================================================================


ORDER_CODE_PATTERN = re.compile(r"^ORD-\d{6}-[0-9A-F]{4}$")




def test_order_code_format():
    with patch.object(shop, "query_one", return_value=None):
        code = shop.generate_order_code()
    assert ORDER_CODE_PATTERN.match(code)




def test_order_code_has_todays_date():
    with patch.object(shop, "query_one", return_value=None):
        code = shop.generate_order_code()
    assert code.split("-")[1] == datetime.now().strftime("%y%m%d")




def test_order_code_retries_when_taken():
    with patch.object(shop, "query_one", side_effect=[{"id": 1}, None]) as fake_query, \
         patch.object(shop.secrets, "token_hex", side_effect=["aaaa", "bbbb"]):
        code = shop.generate_order_code()
    assert fake_query.call_count == 2
    assert code.endswith("-BBBB")
    assert ORDER_CODE_PATTERN.match(code)



