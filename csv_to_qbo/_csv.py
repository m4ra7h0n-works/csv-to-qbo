"""Strict single-account CSV input."""
import csv
import hashlib
import re
from collections import Counter
from datetime import date
from decimal import Decimal


def read_transactions(source, account_id):
    rows, occurrences = [], Counter()
    with source.open(encoding="utf-8-sig", newline="") as input_file:
        reader = csv.reader(input_file, strict=True)
        if next(reader, []) != ["date", "description", "amount"]:
            raise ValueError("Require exactly the headers date,description,amount in that order.")
        for number, cells in enumerate(reader, 2):
            if len(cells) != 3:
                raise ValueError(f"Row {number}: expected three columns.")
            day, description, amount = cells
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day):
                raise ValueError(f"Row {number}: dates must use YYYY-MM-DD.")
            date.fromisoformat(day)
            if not description.strip() or len(description) > 255 or any(ord(ch) < 32 for ch in description):
                raise ValueError(f"Row {number}: require a nonempty single-line description, up to 255 characters.")
            if not re.fullmatch(r"[+-]?[0-9]{1,13}(?:\.[0-9]{1,2})?", amount):
                raise ValueError(f"Row {number}: require dot-decimal signed amounts with at most two decimal places.")
            amount = format(Decimal(amount), ".2f")
            identity = (account_id, day, description, amount)
            occurrences[identity] += 1
            fitid = hashlib.sha256(("\0".join(identity) + "\0" + str(occurrences[identity])).encode()).hexdigest()[:32]
            rows.append((day, description, amount, fitid))
    if not rows:
        raise ValueError("No transactions found.")
    return rows
