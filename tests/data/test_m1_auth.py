# test_m1_auth.py
import csv
import os
import sys
import pytest

from unittest.mock import patch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import app as shop

DATA = os.path.join(ROOT, "tests", "data")

def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

# ---------- 1.1 is_valid_email ----------

def test_is_valid_email_from_csv():
    for row in read_csv("is_valid_email.csv"):
        value = row["input"]
        if value == "<NONE>":
            value = None

        expected = row["expected"].lower() == "true"
        assert shop.is_valid_email(value) is expected, (
            f"Input={value!r}, expected={expected}"
        )

# ---------- 1.2 password_problem ----------

def test_password_problem_from_csv():
    for row in read_csv("password_problem.csv"):
        value = row["input"]

        if value == "<NONE>":
            value = None
        elif value == "<LEN72_VALID>":
            value = "a" * 71 + "1"
        elif value == "<LEN73>":
            value = "a" * 72 + "1"
        elif value == "<SPACES6>":
            value = " " * 6
        elif value == "<UNICODE>":
            value = "پاسورڈ1"

        result = shop.password_problem(value)
        expected = row["expected"]

        if expected == "OK":
            assert result == "", f"Input={value!r}, got={result!r}"
        else:
            assert expected.lower() in result.lower(), (
                f"Input={value!r}, expected message containing "
                f"{expected!r}, got {result!r}"
            )

# ---------- 1.3 safe_next_url ----------

def test_safe_next_url_from_csv():
    for row in read_csv("safe_next_url.csv"):
        value = row["input"]
        if value == "<NONE>":
            value = None

        expected = row["expected"]
        if expected == "<NONE>":
            expected = None

        assert shop.safe_next_url(value) == expected

@pytest.mark.xfail(
    strict=False,
    reason="Security defect: /\\evil.com may be interpreted as //evil.com"
)
def test_safe_next_url_backslash_attack():
    assert shop.safe_next_url("/\\evil.com") is None

# ---------- Basic function-level sanity checks ----------

def test_is_valid_email_none():
    assert shop.is_valid_email(None) is False

def test_password_problem_none():
    assert "at least 6 characters" in shop.password_problem(None).lower()

def test_safe_next_url_relative_path():
    assert shop.safe_next_url("/cart") == "/cart"

def test_safe_next_url_protocol_relative():
    assert shop.safe_next_url("//evil.com") is None

# ---------- Route tests ----------
# These use conventional field names. Adjust them if app.py
# uses different form names or a different CSRF mechanism.

@pytest.fixture
def client():
    shop.app.config["TESTING"] = True
    return shop.app.test_client()

def valid_registration():
    return {
        "name": "Noor Ali",
        "email": "noor@example.com",
        "phone": "1234567890",
        "password": "abc123",
        "confirm_password": "abc123",
    }

def test_register_valid(client):
    with patch.object(shop, "query_one", return_value=None), \
         patch.object(shop, "execute") as fake_execute:
        response = client.post(
            "/register",
            data=valid_registration(),
            follow_redirects=False,
        )

    assert response.status_code in (302, 303)
    assert response.headers["Location"].endswith("/login")
    fake_execute.assert_called_once()

def test_register_duplicate_email(client):
    with patch.object(shop, "query_one", return_value={"id": 1}), \
         patch.object(shop, "execute") as fake_execute:
        response = client.post(
            "/register",
            data=valid_registration(),
            follow_redirects=True,
        )

    assert b"already exists" in response.data.lower()
    fake_execute.assert_not_called()

def test_register_invalid_email(client):
    data = valid_registration()
    data["email"] = "not-an-email"

    with patch.object(shop, "execute") as fake_execute:
        response = client.post(
            "/register", data=data, follow_redirects=True
        )

    assert b"valid email address" in response.data.lower()
    fake_execute.assert_not_called()

def test_register_password_mismatch(client):
    data = valid_registration()
    data["confirm_password"] = "different123"

    with patch.object(shop, "execute") as fake_execute:
        response = client.post(
            "/register", data=data, follow_redirects=True
        )

    assert b"do not match" in response.data.lower()
    fake_execute.assert_not_called()
