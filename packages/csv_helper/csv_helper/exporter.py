
import csv
import io
import math


def safe_csv_value(value):
    if value is None:
        return ""

    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("Unsupported CSV value")

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Invalid numeric value")

    # Prevent spreadsheet applications from interpreting
    # user-controlled text as formulas.
    if isinstance(value, str):
        if value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value

    return value


def generate_csv(rows: list[dict]) -> str:
    if not isinstance(rows, list) or not rows:
        raise ValueError("Dataset must contain rows")

    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Each row must be an object")

    columns = list(rows[0].keys())

    if not columns or not all(
        isinstance(column, str) and column
        for column in columns
    ):
        raise ValueError("Invalid column names")

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(columns)

    for row in rows:
        if set(row.keys()) != set(columns):
            raise ValueError(
                "All rows must contain the same columns"
            )

        writer.writerow([
            safe_csv_value(row[column])
            for column in columns
        ])

    return output.getvalue()

import csv
import io
import math


def safe_csv_value(value):
    if value is None:
        return ""

    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("Unsupported CSV value")

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Invalid numeric value")

    # Prevent spreadsheet applications from interpreting
    # user-controlled text as formulas.
    if isinstance(value, str):
        if value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value

    return value


def generate_csv(rows: list[dict]) -> str:
    if not isinstance(rows, list) or not rows:
        raise ValueError("Dataset must contain rows")

    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Each row must be an object")

    columns = list(rows[0].keys())

    if not columns or not all(
        isinstance(column, str) and column
        for column in columns
    ):
        raise ValueError("Invalid column names")

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(columns)

    for row in rows:
        if set(row.keys()) != set(columns):
            raise ValueError(
                "All rows must contain the same columns"
            )

        writer.writerow([
            safe_csv_value(row[column])
            for column in columns
        ])

    return output.getvalue()
