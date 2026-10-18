"""
======================================================================
 admin_setup.py - Create your ADMIN (and first customer) account
======================================================================

WHY A SEPARATE SCRIPT?
---------------------
We never want a hard-coded admin password sitting in the source code
(or in seed.sql). Instead you run this script ONCE from the terminal
and type the password you want. The script hashes it and saves it
safely in the users table.

HOW TO RUN
    python admin_setup.py

THEN LOG IN
    http://127.0.0.1:5000/login      (the admin is sent to /admin)
"""

import getpass
import sys

from mysql.connector import Error as MySQLError, connect
from werkzeug.security import generate_password_hash

from config import config


def connect_to_database():
    """Open a connection using the credentials from your .env file."""
    return connect(
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
    )


def password_problem(password):
    """Same simple strength rules the registration form uses."""
    if len(password) < 6:
        return "Password must be at least 6 characters long."
    if not any(char.isalpha() for char in password):
        return "Password must contain at least one letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one number."
    return ""


def create_account(is_admin):
    """Ask for the details and insert one new account."""
    print()
    print("=" * 52)
    print("  CREATE A NEW ADMIN ACCOUNT" if is_admin else "  CREATE A CUSTOMER ACCOUNT")
    print("=" * 52)

    name = input("Full name        : ").strip()
    email = input("Email address    : ").strip().lower()
    phone = input("Phone (optional) : ").strip()

    while True:
        password = getpass.getpass("Password         : ")
        problem = password_problem(password)
        if problem:
            print(f"  !  {problem}")
            continue

        if password != getpass.getpass("Confirm password : "):
            print("  !  The passwords do not match. Try again.\n")
            continue
        break

    if not name or "@" not in email:
        print("  !  Name and a valid email are required.")
        return None

    try:
        cursor = connect_to_database().cursor()
        cursor.execute(
            """INSERT INTO users (name, email, password, phone, is_admin)
               VALUES (%s, %s, %s, %s, %s)""",
            (name, email, generate_password_hash(password), phone or None,
             1 if is_admin else 0),
        )
        connection = cursor.connection
        connection.commit()
        cursor.close()
        connection.close()
        print(f"\n  SUCCESS - {email} created as "
              f"{'ADMIN' if is_admin else 'customer'}.\n")
        return email
    except MySQLError as error:
        if error.errno == 1062:
            print(f"\n  !  An account with '{email}' already exists.")
        else:
            print(f"\n  !  Database error: {error}")
        return None


def main():
    print()
    print("======================================================================")
    print(f"  {config['SITE_NAME']}  -  account setup")
    print("======================================================================")

    try:
        connect_to_database().close()
    except MySQLError as error:
        print("\n  !  Could not connect to MySQL.")
        print(f"     {error}")
        print("\n  Check these three things:")
        print("    1. Is the MySQL service running?")
        print("    2. Does your .env file have the right password?")
        print("    3. Have you run database/schema.sql already?")
        sys.exit(1)

    print("\n  1 = Admin account (can manage the shop)")
    print("  2 = Customer account (normal shopping)")
    print("  3 = Create one of each")
    choice = input("\nChoose an option [1-3]: ").strip() or "1"

    if choice == "1":
        create_account(is_admin=True)
    elif choice == "2":
        create_account(is_admin=False)
    elif choice == "3":
        create_account(is_admin=True)
        create_account(is_admin=False)
    else:
        print("\n  Nothing was created.\n")


if __name__ == "__main__":
    main()