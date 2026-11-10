"""Command-line entry point."""
import argparse
import csv
import sys

from . import convert


def main():
    parser = argparse.ArgumentParser(description="CSV to QBO with your actual closing balance; QuickBooks import unverified.")
    parser.add_argument("input")
    parser.add_argument("output", help="New .qbo path; existing files are never overwritten")
    for name in ("bank-id", "account-id", "fid", "org", "intu-bid"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--closing-balance", required=True, help="Actual closing ledger balance, signed dot-decimal amount")
    parser.add_argument("--balance-date", required=True, help="Date of that balance, YYYY-MM-DD; on or after every transaction")
    args = parser.parse_args()
    try:
        count = convert(args.input, args.output, bank_id=args.bank_id, account_id=args.account_id,
                        fid=args.fid, org=args.org, intu_bid=args.intu_bid, currency=args.currency,
                        closing_balance=args.closing_balance, balance_date=args.balance_date)
    except (ValueError, OSError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} transactions with your supplied ledger balance. Real QuickBooks import has not been verified.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
