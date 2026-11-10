# csv-to-qbo

Convert one checking-account CSV to a QBO statement with a supplied ledger balance; QuickBooks import unverified.

**Import status:** The output includes the sign-on response, bank/account identity, dated transaction list and `LEDGERBAL` with your actual closing balance and its date. It has not been verified by importing into a real QuickBooks account. A complete statement structure does not guarantee bank or Intuit acceptance. No balance is invented or calculated from transaction totals.

## Install

Python 3.10 or newer. From this repository:

```sh
python -m venv .venv
# Activate .venv using your shell's activation command, then:
python -m pip install .
```

No runtime dependencies beyond Python's standard library. It also runs directly from the repository.

## Usage

```sh
python -m csv_to_qbo examples/transactions.csv transactions.qbo \
  --bank-id 000000000 --account-id 000001 --fid 00000 \
  --org "Fictional Bank" --intu-bid 00000 \
  --closing-balance 587.50 --balance-date 2026-01-31
```

These example identifiers and transactions are entirely fictional and only for inspecting the output. For your own file, supply your actual account and bank identifiers and a bank-authorized Intuit BID. Do not guess identifiers or use the fictional ones for a real import. `--closing-balance` and `--balance-date` are required: copy the real closing ledger balance and its corresponding date from your statement, in the same account currency. The date must be on or after every exported transaction. For a negative balance, use e.g. `--closing-balance=-125.25`. `--currency` defaults to `USD`; this does not convert currencies.

The output path must be new. Existing files are never overwritten. All conversion runs locally; the CLI makes no network requests. Errors exit with code 2. A successful export reminds you that real QuickBooks import has not been verified. Run `python -m csv_to_qbo --help` for arguments.

Importable API (returns transaction count):

```python
from csv_to_qbo import convert

convert("examples/transactions.csv", "transactions.qbo",
        bank_id="000000000", account_id="000001", fid="00000",
        org="Fictional Bank", intu_bid="00000", currency="USD",
        closing_balance="587.50", balance_date="2026-01-31")
```

Input must use these exact, ordered headers:

```csv
date,description,amount
2026-01-02,Sample supplies,-12.50
2026-01-03,Sample refund,100.00
```

See [examples/transactions.qbo](examples/transactions.qbo) for the full fictional output. An excerpt:

```text
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260102120000
<TRNAMT>-12.50
```

## Capabilities and limits

- One checking account and one currency per invocation, supplied through CLI arguments. The CSV cannot contain an account column. Savings and credit-card account types are not supported by this CLI.
- UTF-8 comma CSV (optional BOM) only; the exact headers are `date,description,amount`. Blank data rows, extra columns and invalid rows stop the whole export.
- Only `YYYY-MM-DD` dates. Signed dot-decimal amounts with at most two decimal places, up to 13 integer digits: negative means money out, positive means money in. No date-order selection, sign reversal, separate debit/credit columns, thousands separators or decimal-comma parsing.
- A nonempty single-line description of at most 255 characters. Output is OFX 1.x SGML in Windows-1252 with a `.qbo` extension, including supplied FI / Intuit identifiers. Text that cannot be encoded is rejected. Markup is escaped. NAME is truncated to 32 characters; MEMO retains the full description.
- Duplicate rows are kept. FITIDs are deterministic hashes of account ID, date, description, normalized amount and an occurrence counter for identical rows. They are not bank-issued transaction IDs and cannot guarantee deduplication across overlapping exports or other tools. The OFX server timestamp changes on each run.
- The required balance parameters are strings: a signed dot-decimal amount with at most two decimal places and up to 13 integer digits, and a `YYYY-MM-DD` date. An explicitly supplied zero or negative balance is accepted. The statement end date and `LEDGERBAL/DTASOF` use that date; `LEDGERBAL/BALAMT` uses your supplied amount. There is no balance reconciliation.
- No XLSX input, preview, duplicate review, normalized spreadsheet output or QFX/OFX output option. There is no direct bank connection, and this project is not affiliated with Intuit.

## This CLI vs Online version

| Feature | This CLI | Online version |
| --- | --- | --- |
| Input | Fixed-header CSV | CSV or values-only, single-sheet XLSX |
| Account and currency | One checking account and currency | One account and currency; checking, savings or credit card |
| Dates and signs | YYYY-MM-DD, signed amount | Date order, decimal separator, sign controls, debit/credit mapping |
| Duplicate rows | Keeps all; no review | Review and keep/remove exact repeats |
| Preview and validation | CLI errors; no preview | Checked preview, source rows, mappings and skipped-row review |
| Output | QBO statement with supplied ledger balance; import unverified | Normalized CSV/XLSX; QBO, QFX or OFX |
| Actual closing balance | Required, with corresponding date | Required to generate statement-format QBO/QFX/OFX |
| Guaranteed bank / Intuit acceptance | No | No |

## Online version

[CSVqbo online](https://csvqbo.pivlu.com/?utm_source=github&utm_medium=readme&utm_campaign=csv-to-qbo) is a separate online version by the same author, Zijian Xiao. It needs no local installation and includes a preview with mapping, date, sign, duplicate and skipped-row checks. It generates QBO, QFX or OFX using your supplied bank identity and actual ledger balance; it does not guarantee bank or Intuit acceptance.

Free allowance, based on the supplied product information dated November 10, 2026:

Free after registration, no card: 2 complete files per account, up to 200 source transactions per file, including preview and all supported download formats. Each site allows 12 successful free files per network address in a rolling 30 days, shared across accounts. Free uploads allow 20 requests per account and network address per hour, including failures and date-order retries. Repeated downloads of the same result and failed conversions use no file allowance. When the free size or allowance is exceeded, buy an existing one-time pack and upload in paid mode. Normal supported-format limits and validation still apply; no free row truncation.

The local MIT-licensed CLI has no online quota. Visiting the link is optional; uploaded online files are processed by the online service.

## Tests

```sh
python -m pip install ".[test]"
python -m pytest
```

## License

MIT. Copyright (c) 2026 Zijian Xiao. See [LICENSE](LICENSE).
