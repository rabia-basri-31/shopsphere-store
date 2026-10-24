import os
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)

for path in (PROJECT_ROOT, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

MODULE_ORDER = ["m3", "m1", "m2"]
LEVEL_ORDER = ["unit", "route", "security"]
DEFAULT_PRIORITY = 5


def module_group(item):
    for name in MODULE_ORDER:
        if item.get_closest_marker(name):
            return name
    return None


def sort_key(item):
    group = module_group(item)
    module_rank = MODULE_ORDER.index(group) if group else len(MODULE_ORDER)

    priority_marker = item.get_closest_marker("priority")
    priority = priority_marker.args[0] if priority_marker else DEFAULT_PRIORITY

    level_rank = len(LEVEL_ORDER)
    for index, level in enumerate(LEVEL_ORDER):
        if item.get_closest_marker(level):
            level_rank = index
            break

    return (module_rank, priority, level_rank)


def pytest_collection_modifyitems(config, items):
    for item in items:
        group = module_group(item)
        if group:
            item.add_marker(pytest.mark.xdist_group(group))
    items.sort(key=sort_key)
