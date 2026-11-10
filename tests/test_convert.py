import re
import subprocess
import sys
from pathlib import Path

import pytest

from csv_to_qbo import convert

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
IDENTITY = dict(bank_id="000000000", account_id="000001", fid="00000", org="Fictional Bank", intu_bid="00000",
                closing_balance="587.50", balance_date="2026-01-31")


def test_example_and_balance_boundary(tmp_path):
    output = tmp_path / "transactions.qbo"
    assert convert(EXAMPLES / "transactions.csv", output, **IDENTITY) == 2
    text = output.read_text(encoding="cp1252")
    expected = (EXAMPLES / "transactions.qbo").read_text(encoding="cp1252")
    assert re.sub(r"<DTSERVER>\d+", "<DTSERVER>TIME", text) == re.sub(r"<DTSERVER>\d+", "<DTSERVER>TIME", expected)
    assert "<TRNTYPE>DEBIT" in text and "<TRNTYPE>CREDIT" in text
    assert "</BANKTRANLIST>\n<LEDGERBAL>\n<BALAMT>587.50\n<DTASOF>20260131120000\n</LEDGERBAL>\n</STMTRS>" in text
    assert "<DTEND>20260131120000" in text
    assert "<INTU.BID>00000" in text
    assert text.count("<STMTTRN>") == 2
    assert "<ACCTID>000001" in text


def test_preserves_duplicates_and_escapes_markup(tmp_path):
    source, output = tmp_path / "transactions.csv", tmp_path / "transactions.qbo"
    source.write_text("date,description,amount\n2026-01-02,Sample <tag> & supplies,-1\n2026-01-02,Sample <tag> & supplies,-1\n")
    assert convert(source, output, **IDENTITY) == 2
    text = output.read_text()
    assert "Sample &lt;tag&gt; &amp; supplies" in text
    assert len(set(re.findall(r"<FITID>([^\n]+)", text))) == 2


@pytest.mark.parametrize("field,value", [("bank_id", ""), ("intu_bid", "bad<"), ("account_id", "x" * 23), ("org", "\n"), ("currency", "usd")])
def test_bad_identity(tmp_path, field, value):
    identity = {**IDENTITY, field: value}
    output = tmp_path / "transactions.qbo"
    with pytest.raises(ValueError):
        convert(EXAMPLES / "transactions.csv", output, **identity)
    assert not output.exists()


def test_no_overwrite_and_only_qbo(tmp_path):
    output = tmp_path / "transactions.qbo"
    output.write_text("keep")
    with pytest.raises(FileExistsError):
        convert(EXAMPLES / "transactions.csv", output, **IDENTITY)
    assert output.read_text() == "keep"
    with pytest.raises(ValueError):
        convert(EXAMPLES / "transactions.csv", output.with_suffix(".ofx"), **IDENTITY)


def test_invalid_data_and_unencodable_text_leave_no_output(tmp_path):
    source, output = tmp_path / "source.csv", tmp_path / "output.qbo"
    for line in ["2026-01-02,Sample,NaN", "2026-01-02,\u6837\u4f8b,1.00"]:
        source.write_text("date,description,amount\n" + line + "\n", encoding="utf-8")
        with pytest.raises(ValueError):
            convert(source, output, **IDENTITY)
        assert not output.exists()


def test_cli(tmp_path):
    output = tmp_path / "transactions.qbo"
    args = [sys.executable, "-m", "csv_to_qbo", str(EXAMPLES / "transactions.csv"), str(output)]
    for key, value in IDENTITY.items():
        args.extend(["--" + key.replace("_", "-"), value])
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Real QuickBooks import has not been verified" in result.stderr
    failed = subprocess.run(args, capture_output=True, text=True)
    assert failed.returncode == 2
    assert "Traceback" not in failed.stderr


@pytest.mark.parametrize("field,value", [
    ("closing_balance", ""), ("closing_balance", "NaN"), ("closing_balance", "1.001"),
    ("closing_balance", "1,000.00"), ("closing_balance", 587.5),
    ("balance_date", "2026-02-30"), ("balance_date", "01/31/2026"),
    ("balance_date", "2026-01-02"),
])
def test_invalid_balance_leaves_no_output(tmp_path, field, value):
    output = tmp_path / "transactions.qbo"
    with pytest.raises(ValueError):
        convert(EXAMPLES / "transactions.csv", output, **{**IDENTITY, field: value})
    assert not output.exists()


@pytest.mark.parametrize("balance,expected", [("0", "0.00"), ("-125.25", "-125.25"), ("1000", "1000.00")])
def test_uses_supplied_balance_not_transaction_net(tmp_path, balance, expected):
    output = tmp_path / "transactions.qbo"
    convert(EXAMPLES / "transactions.csv", output, **{**IDENTITY, "closing_balance": balance})
    assert f"<BALAMT>{expected}\n" in output.read_text()


@pytest.mark.parametrize("missing", ["closing_balance", "balance_date"])
def test_balance_parameters_are_required(tmp_path, missing):
    output = tmp_path / "transactions.qbo"
    args = {key: value for key, value in IDENTITY.items() if key != missing}
    with pytest.raises(TypeError):
        convert(EXAMPLES / "transactions.csv", output, **args)
    command = [sys.executable, "-m", "csv_to_qbo", str(EXAMPLES / "transactions.csv"), str(output)]
    for key, value in args.items():
        command.extend(["--" + key.replace("_", "-"), value])
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2
    assert "--" + missing.replace("_", "-") in result.stderr
    assert not output.exists()
