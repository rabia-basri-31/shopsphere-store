from unittest.mock import patch
from urllib.parse import unquote, urlparse

import pytest
from werkzeug.security import generate_password_hash

from helpers import csv_cases

import app as shop

pytestmark = pytest.mark.m1


def check_password(value, expected):
    result = shop.password_problem(value)
    if expected:
        assert expected in result
    else:
        assert result == ""


@pytest.mark.unit
@pytest.mark.boundary
class TestIsValidEmail:

    @pytest.mark.parametrize(
        "value,expected", csv_cases("is_valid_email.csv", "input", "expected")
    )
    def test_from_csv(self, value, expected):
        assert shop.is_valid_email(value) is (expected == "True")

    def test_none(self):
        assert shop.is_valid_email(None) is False


@pytest.mark.unit
@pytest.mark.boundary
class TestPasswordProblem:

    @pytest.mark.parametrize(
        "value,expected",
        csv_cases("password_problem.csv", "input", "expected_contains"),
    )
    def test_from_csv(self, value, expected):
        check_password(value, expected)

    @pytest.mark.parametrize(
        "value,expected",
        [
            pytest.param("a" * 71 + "1", "", id="AU-P3"),
            pytest.param("a" * 72 + "1", "too long (maximum 72", id="AU-P4"),
            pytest.param(None, "at least 6 characters", id="AU-P8"),
        ],
    )
    def test_inline_cases(self, value, expected):
        check_password(value, expected)


@pytest.mark.unit
@pytest.mark.security
class TestSafeNextUrl:

    @pytest.mark.parametrize(
        "value,expected", csv_cases("safe_next_url.csv", "input", "expected")
    )
    def test_from_csv(self, value, expected):
        expected = None if expected == "None" else expected
        assert shop.safe_next_url(value) == expected

    def test_none(self):
        assert shop.safe_next_url(None) is None

    @pytest.mark.xfail(reason="open redirect: /\\evil.com is returned unchanged")
    def test_backslash_prefix(self):
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


@pytest.mark.route
class TestRegister:

    @pytest.mark.smoke
    @pytest.mark.priority(1)
    def test_all_valid(self):
        response, fake_execute, messages = post_register()
        assert response.status_code == 302
        assert urlparse(response.headers["Location"]).path == "/login"
        assert any("Account created!" in m for m in messages)
        fake_execute.assert_called_once()

    @pytest.mark.parametrize(
        "field,value,should_pass,message",
        csv_cases(
            "register_fields.csv", "field", "value", "should_pass", "expected_message"
        ),
    )
    def test_field_rules(self, field, value, should_pass, message):
        response, fake_execute, messages = post_register({field: value})

        if should_pass == "yes":
            assert response.status_code == 302
            fake_execute.assert_called_once()
        else:
            assert response.status_code == 200
            fake_execute.assert_not_called()
            assert any(message in m for m in messages)

    def test_phone_empty_stored_as_none(self):
        response, fake_execute, messages = post_register({"phone": ""})
        assert response.status_code == 302
        assert fake_execute.call_args.args[1][3] is None

    def test_duplicate_email(self):
        response, fake_execute, messages = post_register(duplicate=True)
        assert any("already exists" in m for m in messages)
        fake_execute.assert_not_called()

    def test_email_saved_lowercase(self):
        response, fake_execute, messages = post_register({"email": "ALI@EXAMPLE.COM"})
        assert response.status_code == 302
        assert fake_execute.call_args.args[1][1] == "ali@example.com"


@pytest.mark.route
@pytest.mark.security
class TestRegisterSecurity:

    def test_password_is_hashed(self):
        response, fake_execute, messages = post_register()
        saved_password = fake_execute.call_args.args[1][2]
        assert saved_password != "abc12345"

    def test_missing_csrf(self):
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


@pytest.mark.route
class TestLogin:

    @pytest.mark.parametrize(
        "email,password,user_exists,is_admin,next_value,expected_type,expected",
        csv_cases(
            "login_cases.csv",
            "email",
            "password",
            "user_exists",
            "is_admin",
            "next",
            "expected_type",
            "expected",
        ),
    )
    def test_decision_table(
        self, email, password, user_exists, is_admin, next_value, expected_type, expected
    ):
        user = None if user_exists == "no" else make_user(int(is_admin))
        response, messages, user_id = post_login(email, password, user, next_value)

        if expected_type == "redirect":
            location = response.headers["Location"]
            assert response.status_code == 302
            assert urlparse(location).path == expected
            assert "evil.com" not in location
            assert user_id == 1
        else:
            assert response.status_code == 200
            assert any(expected in m for m in messages)
            assert user_id is None

    @pytest.mark.smoke
    @pytest.mark.priority(1)
    def test_valid_customer(self):
        response, messages, user_id = post_login(
            "ali@example.com", "abc12345", make_user(0)
        )
        assert user_id == 1
        assert urlparse(response.headers["Location"]).path == "/"

    def test_already_logged_in(self):
        with patch.object(shop, "get_current_user", return_value=LOGGED_IN_USER):
            response = shop.app.test_client().get("/login")
        assert response.status_code == 302
        assert urlparse(response.headers["Location"]).path == "/"


@pytest.mark.route
class TestLogout:

    def test_logged_in(self):
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

    def test_guest(self):
        with patch.object(shop, "get_current_user", return_value=None), \
             patch.object(shop, "flash") as fake_flash:
            response = shop.app.test_client().get("/logout")

        assert response.status_code == 302
        assert urlparse(response.headers["Location"]).path == "/"
        fake_flash.assert_not_called()


@pytest.mark.route
@pytest.mark.security
class TestAccessControl:

    def test_same_message_for_unknown_email(self):
        _, wrong_password, _ = post_login("ali@example.com", "wrong999", make_user(0))
        _, unknown_email, _ = post_login("nobody@example.com", "abc12345", None)
        assert wrong_password == unknown_email

    def test_login_required_redirects_guest(self):
        with patch.object(shop, "get_current_user", return_value=None), \
             patch.object(shop, "flash"):
            response = shop.app.test_client().get("/cart")

        location = response.headers["Location"]
        assert response.status_code == 302
        assert urlparse(location).path == "/login"
        assert "next=/cart" in unquote(location)

    def test_admin_required_blocks_customer(self):
        with patch.object(shop, "get_current_user", return_value=LOGGED_IN_USER), \
             patch.object(shop, "render_template", return_value="ok"):
            response = shop.app.test_client().get("/admin")

        assert response.status_code == 403
