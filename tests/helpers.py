import csv
import os

import pytest

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_csv(name):
    file_path = os.path.join(DATA, name)

    with open(file_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def csv_cases(name, *columns):
    cases = []
    for row in read_csv(name):
        values = [row[column] for column in columns]
        cases.append(pytest.param(*values, id=row["id"]))
    return cases
