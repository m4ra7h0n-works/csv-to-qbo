from pathlib import Path

import pytest

from csv_to_qbo._csv import read_transactions

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_example():
    rows = read_transactions(EXAMPLES / "transactions.csv", "000001")
    assert [row[:3] for row in rows] == [("2026-01-02", "Sample supplies", "-12.50"), ("2026-01-03", "Sample refund", "100.00")]


def test_stable_distinct_ids_without_removing_duplicates(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("date,description,amount\n2026-01-02,Sample,-1.00\n2026-01-02,Sample,-1.00\n")
    rows = read_transactions(source, "000001")
    assert len(rows) == 2
    assert rows[0][-1] != rows[1][-1]
    assert rows == read_transactions(source, "000001")
    assert rows[0][-1] != read_transactions(source, "000002")[0][-1]


@pytest.mark.parametrize("text", [
    "date,description,amount\n", "Date,description,amount\n2026-01-02,Sample,1\n",
    "date,description,amount,account\n2026-01-02,Sample,1,00001\n",
    "date,description,amount\n01/02/2026,Sample,1\n",
    "date,description,amount\n2026-02-30,Sample,1\n",
    "date,description,amount\n2026-01-02,Sample,NaN\n",
    "date,description,amount\n2026-01-02,Sample,1.001\n",
    'date,description,amount\n2026-01-02,Sample,"1,23"\n',
    "date,description,amount\n2026-01-02,,1\n",
    'date,description,amount\n2026-01-02,"Sample\nsecond line",1\n',
    "date,description,amount\n2026-01-02,Sample,1\n\n",
])
def test_reject_unsupported(tmp_path, text):
    source = tmp_path / "source.csv"
    source.write_text(text)
    with pytest.raises(ValueError):
        read_transactions(source, "000001")
