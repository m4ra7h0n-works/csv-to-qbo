"""Single-account QBO statements with a caller-supplied ledger balance."""
import html
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from ._csv import read_transactions

__all__ = ["convert"]


def convert(source, target, *, bank_id, account_id, fid, org, intu_bid,
            closing_balance, balance_date, currency="USD"):
    """Write checking-account QBO to a new path; return transaction count.

    Supply the real closing balance and its YYYY-MM-DD date as strings.
    Balances and bank identifiers are never inferred from transactions.
    """
    source, target = Path(source), Path(target)
    if source.suffix.lower() != ".csv" or target.suffix.lower() != ".qbo":
        raise ValueError("Use a .csv input and .qbo output.")
    for label, value, maximum in [("bank_id", bank_id, 20), ("account_id", account_id, 22),
                                   ("fid", fid, 20), ("intu_bid", intu_bid, 20)]:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9-]{1," + str(maximum) + "}", value):
            raise ValueError(f"{label} must contain 1–{maximum} letters, digits or hyphens.")
    if not isinstance(org, str) or not org.strip() or len(org) > 32 or any(ord(ch) < 32 for ch in org):
        raise ValueError("org must be nonempty single-line text, up to 32 characters.")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("Use one uppercase three-letter currency.")
    if not isinstance(closing_balance, str) or not re.fullmatch(r"[+-]?[0-9]{1,13}(?:\.[0-9]{1,2})?", closing_balance):
        raise ValueError("closing_balance must be the actual dot-decimal balance, with at most two decimal places.")
    if not isinstance(balance_date, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", balance_date):
        raise ValueError("balance_date must use YYYY-MM-DD.")
    date.fromisoformat(balance_date)
    rows = read_transactions(source, account_id)
    if balance_date < max(row[0] for row in rows):
        raise ValueError("balance_date cannot precede any transaction date.")
    closing_balance = format(Decimal(closing_balance), ".2f")
    last_date = balance_date.replace("-", "") + "120000"

    def tag(name, value):
        return f"<{name}>" + html.escape(value, quote=False) + "\n"

    output = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n"
    output += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS>\n<CODE>0\n<SEVERITY>INFO\n</STATUS>\n"
    output += tag("DTSERVER", datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")) + tag("LANGUAGE", "ENG") + "<FI>\n"
    output += tag("ORG", org) + tag("FID", fid) + "</FI>\n" + tag("INTU.BID", intu_bid)
    output += "</SONRS>\n</SIGNONMSGSRSV1>\n<BANKMSGSRSV1>\n<STMTTRNRS>\n<TRNUID>1\n<STATUS>\n<CODE>0\n<SEVERITY>INFO\n</STATUS>\n<STMTRS>\n"
    output += tag("CURDEF", currency) + "<BANKACCTFROM>\n" + tag("BANKID", bank_id)
    output += tag("ACCTID", account_id) + tag("ACCTTYPE", "CHECKING") + "</BANKACCTFROM>\n<BANKTRANLIST>\n"
    output += tag("DTSTART", min(row[0] for row in rows).replace("-", "") + "120000") + tag("DTEND", last_date)
    for day, description, amount, fitid in rows:
        output += "<STMTTRN>\n" + tag("TRNTYPE", "DEBIT" if Decimal(amount) < 0 else "CREDIT")
        output += tag("DTPOSTED", day.replace("-", "") + "120000") + tag("TRNAMT", amount)
        output += tag("FITID", fitid) + tag("NAME", description[:32]) + tag("MEMO", description) + "</STMTTRN>\n"
    output += "</BANKTRANLIST>\n<LEDGERBAL>\n" + tag("BALAMT", closing_balance) + tag("DTASOF", last_date)
    output += "</LEDGERBAL>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>\n"
    try:
        encoded = output.encode("cp1252")
    except UnicodeEncodeError:
        raise ValueError("QBO text must fit Windows-1252; unsupported characters are not discarded.") from None
    with target.open("xb") as output_file:
        output_file.write(encoded)
    return len(rows)
