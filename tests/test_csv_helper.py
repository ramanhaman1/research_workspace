
import csv
import io

import pytest

from csv_helper import generate_csv


def test_generate_csv():
    rows = [
        {"participant": 1, "score": 80},
        {"participant": 2, "score": 92},
    ]

    result = generate_csv(rows)

    parsed = list(csv.reader(io.StringIO(result)))

    assert parsed == [
        ["participant", "score"],
        ["1", "80"],
        ["2", "92"],
    ]


def test_csv_formula_protection():
    rows = [
        {"name": "=1+1", "score": 80}
    ]

    result = generate_csv(rows)

    parsed = list(csv.reader(io.StringIO(result)))

    assert parsed[1][0] == "'=1+1"


def test_invalid_columns():
    rows = [
        {"participant": 1},
        {"score": 80},
    ]

    with pytest.raises(ValueError):
        generate_csv(rows)
