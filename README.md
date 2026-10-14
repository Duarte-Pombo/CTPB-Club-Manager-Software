# CTPB Club Manager

A desktop application for managing members, quota payments, and athlete expenses at a tennis club. Members are identified by tapping an NFC card on a reader, which opens their personal dashboard in one step. Everything is stored locally in SQLite, so the app works offline with no server to maintain.

> **Stack:** Python · Tkinter · SQLite · PC/SC (NFC) via `pyscard`

---

## Why this project exists

The club's treasury was tracked by hand: who had paid which month, who owed money for string jobs or court rentals, and what came in over the year. This app replaces that with a single tool that answers the questions the treasurer actually asks:

- *Who still owes quotas for these months?*
- *What does each athlete owe me, and for what?*
- *How did the club do this year, month by month?*

---

## Features

### Members and identification
- **NFC card check-in:** a background thread listens to the reader, and tapping a card opens that member's dashboard. Unknown cards offer to start registration.
- **Member profiles** with name, contact details, NIF, citizen card number, address, and membership type (`admin`, `atleta`, `sócio`, `atleta e sócio`).
- **Edit profiles** from the main list or from inside a member's dashboard, with uniqueness checks on NIF and email.
- **Soft delete:** deactivated members are hidden but their history is preserved.

### Quotas and payments
- **Quota grid per season:** monthly fees, insurance, and annual fee, color-coded as paid, partial, absent/exempt, or unpaid.
- **Partial payments** with "settle remainder" and full cancel/refund flows.
- **Payments by method:** cash, Multibanco, bank transfer, MB Way.

### Debts and expenses
- **Per-athlete debts** for things like court rental, string jobs, overgrips, and bar. Debts stay pending until settled.
- **Edit or delete any transaction** from a right-click menu; the member's balance adjusts automatically.

### Filtering and reports
- **Multi-month overdue filter:** select any combination of months (plus insurance and annual fee) and see exactly which athletes are missing which ones.
- **Printable list export** that includes each athlete's missing months.
- **Monthly report** by category and payment method.
- **Annual report** with month-by-month income and expenses, category breakdown, and net result.
- **Debts report** grouped by athlete with subtotals and a grand total owed to the club.

### Safety and maintenance
- **Audit log** of registrations, edits, deletions, and payments, with an in-app viewer.
- **Backup and restore** of the full database from the UI.
- **Automatic schema migration:** new columns are added to an existing database on startup without losing data.

---

## Architecture

```
main.py             Entry point; starts the UI and the NFC listener thread
dashboard_main.py   Main window: member list, filters, reports, backup tools
user_dashboard.py   Per-member window: quota grid, debts, payment history
users.py            Registration and profile-edit forms, user lookups
db_schema.py        Schema creation, migrations, audit-log helper
```

**Data model (SQLite):** `users`, `transactions`, `monthly_fees`, `payment_types`, `audit_logs`, with foreign keys and indexes on the columns the reports query most.

**Design notes**
- The NFC reader runs in a daemon thread and hands card IDs to the Tkinter main loop with `after(0, ...)`, since Tkinter is not thread-safe.
- Database access uses a connection timeout and `sqlite3.Row`, so rows support both positional and by-name access, and adding columns does not break existing code.
- Registration and editing share one form base class so both stay consistent.

---

## Getting started

**Requirements**
- Python 3.9+ with Tkinter
- A PC/SC-compatible NFC reader (optional; the app runs without one, you just lose card taps)
- `pyscard`

```bash
pip install pyscard
```

**Run**

```bash
# 1. Create (or upgrade) the database
python db_schema.py

# 2. Launch the app
python main.py
```

On Linux, the reader also needs the PC/SC daemon (`pcscd`) running.

---

## Author

**Duarte**
[GitHub](https://github.com/your-username) · [LinkedIn](https://www.linkedin.com/in/your-profile)
