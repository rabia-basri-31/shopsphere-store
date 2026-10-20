import csv
import os
import sys
from unittest.mock import patch
from urllib.parse import unquote, urlparse

import pytest
from werkzeug.security import generate_password_hash

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import app as shop


DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_csv(name):
    file_path = os.path.join(DATA, name)

    with open(file_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_email_from_csv():
    for row in read_csv("is_valid_email.csv"):
        assert str(shop.is_valid_email(row["input"])) == row["expected"], row["id"]


def test_email_typical():
    assert shop.is_valid_email("user@example.com") is True


def test_email_shortest_tld():
    assert shop.is_valid_email("a@b.co") is True


def test_email_one_letter_tld():
    assert shop.is_valid_email("a@b.c") is False


def test_email_no_at():
    assert shop.is_valid_email("abc.example.com") is False


def test_email_two_at():
    assert shop.is_valid_email("a@@b.com") is False


def test_email_space():
    assert shop.is_valid_email("a b@c.com") is False


def test_email_digits_in_tld():
    assert shop.is_valid_email("a@b.c0m") is False


def test_email_empty():
    assert shop.is_valid_email("") is False


def test_email_none():
    assert shop.is_valid_email(None) is False


def test_email_trailing_space():
    assert shop.is_valid_email("a@b.com ") is False


def test_password_from_csv():
    for row in read_csv("password_problem.csv"):
        result = shop.password_problem(row["input"])
        if row["expected_contains"] == "":
            assert result == "", row["id"]
        else:
            assert row["expected_contains"] in result, row["id"]


def test_password_length_5():
    assert "at least 6 characters" in shop.password_problem("abc12")


def test_password_length_6():
    assert shop.password_problem("abc123") == ""


def test_password_length_72():
    assert shop.password_problem("a" * 71 + "1") == ""


def test_password_length_73():
    assert "too long (maximum 72" in shop.password_problem("a" * 72 + "1")


def test_password_letters_only():
    assert "at least one number" in shop.password_problem("abcdef")


def test_password_digits_only():
    assert "at least one letter" in shop.password_problem("123456")


def test_password_empty():
    assert "at least 6 characters" in shop.password_problem("")


def test_password_none():
    assert "at least 6 characters" in shop.password_problem(None)


def test_password_only_spaces():
    assert "at least one letter" in shop.password_problem("      ")


def test_password_unicode_letters():
    assert shop.password_problem("پاسورڈ1") == ""


def test_next_url_from_csv():
    for row in read_csv("safe_next_url.csv"):
        assert str(shop.safe_next_url(row["input"])) == row["expected"], row["id"]


def test_next_url_relative():
    assert shop.safe_next_url("/cart") == "/cart"


def test_next_url_protocol_relative():
    assert shop.safe_next_url("//evil.com") is None


def test_next_url_absolute():
    assert shop.safe_next_url("http://evil.com") is None


def test_next_url_none():
    assert shop.safe_next_url(None) is None


def test_next_url_empty():
    assert shop.safe_next_url("") is None


def test_next_url_no_leading_slash():
    assert shop.safe_next_url("cart") is None


def test_next_url_root():
    assert shop.safe_next_url("/") == "/"


@pytest.mark.xfail(reason="open redirect: /\\evil.com is returned unchanged")
def test_next_url_backslash():
    assert shop.safe_next_url("/\\evil.com") is None


VALID_REGISTER = {
    "name": "Ali Khan",
    "email": "ali@example.com",
    "phone": "3001234567",
    "password": "abc12345",
    "confirm_password": "abc12345",
    "address": "House 12, Street 4",
}


def post_register(changes=None, duplicate=False, send_token=True):
    form = dict(VALID_REGISTER)
    form.update(changes or {})
    if send_token:
        form["csrf_token"] = "tok"

    existing = {"id": 1} if duplicate else None

    with patch.object(shop, "get_current_user", return_value=None), \
         patch.object(shop, "query_one", return_value=existing), \
         patch.object(shop, "execute", return_value=(1, 1)) as fake_execute, \
         patch.object(shop, "render_template", return_value="ok"), \
         patch.object(shop, "flash") as fake_flash:
        client = shop.app.test_client()
        with client.session_transaction() as sess:
            sess["_csrf_token"] = "tok"
        response = client.post("/register", data=form)

    messages = [call.args[0] for call in fake_flash.call_args_list]
    return response, fake_execute, messages


def test_register_all_valid():
    response, fake_execute, messages = post_register()
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/login"
    assert any("Account created!" in m for m in messages)
    fake_execute.assert_called_once()


def test_register_fields_from_csv():
    for row in read_csv("register_fields.csv"):
        response, fake_execute, messages = post_register({row["field"]: row["value"]})

        if row["should_pass"] == "yes":
            assert response.status_code == 302, row["id"]
            fake_execute.assert_called_once()
        else:
            assert response.status_code == 200, row["id"]
            fake_execute.assert_not_called()
            assert any(row["expected_message"] in m for m in messages), row["id"]


def test_register_name_one_char():
    response, fake_execute, messages = post_register({"name": "A"})
    assert any("full name (at least 2" in m for m in messages)
    fake_execute.assert_not_called()


def test_register_name_two_chars():
    response, fake_execute, messages = post_register({"name": "Al"})
    assert response.status_code == 302
    fake_execute.assert_called_once()


def test_register_invalid_email():
    response, fake_execute, messages = post_register({"email": "bad"})
    assert any("valid email address" in m for m in messages)
    fake_execute.assert_not_called()


def test_register_phone_9_digits():
    response, fake_execute, messages = post_register({"phone": "123456789"})
    assert any("exactly 10 digits" in m for m in messages)


def test_register_phone_11_digits():
    response, fake_execute, messages = post_register({"phone": "12345678901"})
    assert any("exactly 10 digits" in m for m in messages)


def test_register_phone_letters():
    response, fake_execute, messages = post_register({"phone": "abcdefghij"})
    assert any("exactly 10 digits" in m for m in messages)


def test_register_phone_empty_stored_as_none():
    response, fake_execute, messages = post_register({"phone": ""})
    assert response.status_code == 302
    assert fake_execute.call_args.args[1][3] is None


def test_register_password_mismatch():
    response, fake_execute, messages = post_register({"confirm_password": "different1"})
    assert any("do not match" in m for m in messages)
    fake_execute.assert_not_called()


def test_register_duplicate_email():
    response, fake_execute, messages = post_register(duplicate=True)
    assert any("already exists" in m for m in messages)
    fake_execute.assert_not_called()


def test_register_email_saved_lowercase():
    response, fake_execute, messages = post_register({"email": "ALI@EXAMPLE.COM"})
    assert response.status_code == 302
    assert fake_execute.call_args.args[1][1] == "ali@example.com"


def test_register_password_is_hashed():
    response, fake_execute, messages = post_register()
    saved_password = fake_execute.call_args.args[1][2]
    assert saved_password != "abc12345"


def test_register_missing_csrf():
    response, fake_execute, messages = post_register(send_token=False)
    assert response.status_code == 400
    fake_execute.assert_not_called()


PASSWORD_HASH = generate_password_hash("abc12345")

LOGGED_IN_USER = {
    "id": 1,
    "name": "Ali Khan",
    "email": "ali@example.com",
    "phone": "3001234567",
    "address": "House 12",
    "is_admin": 0,
}


def make_user(is_admin=0):
    return {
        "id": 1,
        "name": "Ali Khan",
        "email": "ali@example.com",
        "password": PASSWORD_HASH,
        "is_admin": is_admin,
    }


def post_login(email, password, user, next_value=""):
    form = {
        "email": email,
        "password": password,
        "next": next_value,
        "csrf_token": "tok",
    }

    with patch.object(shop, "get_current_user", return_value=None), \
         patch.object(shop, "query_one", return_value=user), \
         patch.object(shop, "render_template", return_value="ok"), \
         patch.object(shop, "flash") as fake_flash:
        client = shop.app.test_client()
        with client.session_transaction() as sess:
            sess["_csrf_token"] = "tok"
        response = client.post("/login", data=form)
        with client.session_transaction() as sess:
            user_id = sess.get("user_id")

    messages = [call.args[0] for call in fake_flash.call_args_list]
    return response, messages, user_id


def test_login_from_csv():
    for row in read_csv("login_cases.csv"):
        user = None if row["user_exists"] == "no" else make_user(int(row["is_admin"]))
        response, messages, user_id = post_login(
            row["email"], row["password"], user, row["next"]
        )

        if row["expected_type"] == "redirect":
            assert response.status_code == 302, row["id"]
            assert urlparse(response.headers["Location"]).path == row["expected"], row["id"]
            assert user_id == 1, row["id"]
        else:
            assert response.status_code == 200, row["id"]
            assert any(row["expected"] in m for m in messages), row["id"]
            assert user_id is None, row["id"]


def test_login_valid_customer():
    response, messages, user_id = post_login("ali@example.com", "abc12345", make_user(0))
    assert user_id == 1
    assert urlparse(response.headers["Location"]).path == "/"


def test_login_valid_admin():
    response, messages, user_id = post_login("ali@example.com", "abc12345", make_user(1))
    assert urlparse(response.headers["Location"]).path == "/admin"


def test_login_with_next():
    response, messages, user_id = post_login(
        "ali@example.com", "abc12345", make_user(0), "/cart"
    )
    assert urlparse(response.headers["Location"]).path == "/cart"


def test_login_with_evil_next():
    response, messages, user_id = post_login(
        "ali@example.com", "abc12345", make_user(0), "//evil.com"
    )
    assert urlparse(response.headers["Location"]).path == "/"
    assert "evil.com" not in response.headers["Location"]


def test_login_wrong_password():
    response, messages, user_id = post_login("ali@example.com", "wrong999", make_user(0))
    assert "Incorrect email or password." in messages
    assert user_id is None


def test_login_unknown_email_same_message():
    _, wrong_password_messages, _ = post_login("ali@example.com", "wrong999", make_user(0))
    _, unknown_email_messages, _ = post_login("nobody@example.com", "abc12345", None)
    assert wrong_password_messages == unknown_email_messages


def test_login_empty_email():
    response, messages, user_id = post_login("", "abc12345", make_user(0))
    assert any("enter both" in m for m in messages)


def test_login_empty_password():
    response, messages, user_id = post_login("ali@example.com", "", make_user(0))
    assert any("enter both" in m for m in messages)


def test_login_already_logged_in():
    with patch.object(shop, "get_current_user", return_value=LOGGED_IN_USER):
        response = shop.app.test_client().get("/login")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/"


def test_logout_logged_in():
    with patch.object(shop, "get_current_user", return_value=LOGGED_IN_USER), \
         patch.object(shop, "flash") as fake_flash:
        client = shop.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = 1
        response = client.get("/logout")
        with client.session_transaction() as sess:
            remaining = sess.get("user_id")

    messages = [call.args[0] for call in fake_flash.call_args_list]
    assert response.status_code == 302
    assert remaining is None
    assert any("logged out" in m for m in messages)


def test_logout_guest():
    with patch.object(shop, "get_current_user", return_value=None), \
         patch.object(shop, "flash") as fake_flash:
        response = shop.app.test_client().get("/logout")

    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/"
    fake_flash.assert_not_called()


def test_login_required_guest_redirected():
    with patch.object(shop, "get_current_user", return_value=None), \
         patch.object(shop, "flash"):
        response = shop.app.test_client().get("/cart")

    location = response.headers["Location"]
    assert response.status_code == 302
    assert urlparse(location).path == "/login"
    assert "next=/cart" in unquote(location)


def test_admin_required_customer_blocked():
    with patch.object(shop, "get_current_user", return_value=LOGGED_IN_USER), \
         patch.object(shop, "render_template", return_value="ok"):
        response = shop.app.test_client().get("/admin")

    assert response.status_code == 403
