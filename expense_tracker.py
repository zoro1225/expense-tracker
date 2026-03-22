#!/usr/bin/env python3
"""
SkyCash — CLI Expense Tracker
Author: Shivam Bande (zoro1225)
"""

import sqlite3
import csv
import os
import sys
from datetime import datetime, date
from pathlib import Path

# ── Colors ───────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"
    BG_RED = "\033[41m"

def c(color, text):
    return f"{color}{text}{C.RESET}"

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = Path.home() / ".skycash.db"

CATEGORIES = [
    "Food", "Transport", "Shopping", "Entertainment",
    "Health", "Bills", "Education", "Travel", "Other"
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            amount      REAL    NOT NULL,
            description TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            month    TEXT    NOT NULL UNIQUE,
            amount   REAL    NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# ── Helpers ──────────────────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print(c(C.CYAN, C.BOLD + """
╔═══════════════════════════════════════╗
║     💰  SkyCash Expense Tracker       ║
║        by Shivam Bande                ║
╚═══════════════════════════════════════╝"""))

def divider(width=45):
    print(c(C.GRAY, "─" * width))

def success(msg): print(c(C.GREEN,  f"  ✅  {msg}"))
def error(msg):   print(c(C.RED,    f"  ❌  {msg}"))
def warn(msg):    print(c(C.YELLOW, f"  ⚠️   {msg}"))
def info(msg):    print(c(C.CYAN,   f"  ℹ️   {msg}"))

def pick_category():
    print(c(C.BOLD, "\n  Select category:"))
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"    {c(C.CYAN, str(i))}. {cat}")
    while True:
        try:
            choice = int(input(c(C.YELLOW, "\n  Enter number: ")))
            if 1 <= choice <= len(CATEGORIES):
                return CATEGORIES[choice - 1]
            error("Invalid choice.")
        except ValueError:
            error("Enter a number.")

def get_month(prompt="Month (YYYY-MM) [blank = current]: "):
    val = input(c(C.YELLOW, f"  {prompt}")).strip()
    if not val:
        return date.today().strftime("%Y-%m")
    try:
        datetime.strptime(val, "%Y-%m")
        return val
    except ValueError:
        error("Invalid format. Using current month.")
        return date.today().strftime("%Y-%m")

def format_amount(amount):
    return c(C.GREEN, f"Rs.{amount:,.2f}")

def spend_bar(spent, budget, width=30):
    if budget <= 0:
        return ""
    pct = min(spent / budget, 1.0)
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    color = C.GREEN if pct < 0.7 else C.YELLOW if pct < 0.9 else C.RED
    return f"{c(color, bar)} {pct*100:.0f}%"

# ── Features ──────────────────────────────────────────────────────────────────

def add_expense():
    clear(); banner()
    print(c(C.BOLD, "\n  Add New Expense\n"))
    divider()

    while True:
        try:
            amount = float(input(c(C.YELLOW, "  Amount (Rs.): ")))
            if amount <= 0: raise ValueError
            break
        except ValueError:
            error("Enter a valid positive amount.")

    desc = input(c(C.YELLOW, "  Description: ")).strip()
    if not desc:
        error("Description cannot be empty.")
        input(c(C.GRAY, "\n  Press Enter to continue...")); return

    category = pick_category()

    date_input = input(c(C.YELLOW, "  Date (YYYY-MM-DD) [blank = today]: ")).strip()
    if not date_input:
        exp_date = date.today().isoformat()
    else:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            exp_date = date_input
        except ValueError:
            warn("Invalid date, using today.")
            exp_date = date.today().isoformat()

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (amount, description, category, date) VALUES (?, ?, ?, ?)",
        (amount, desc, category, exp_date)
    )
    conn.commit()

    # Budget alert check
    month = exp_date[:7]
    row = conn.execute("SELECT amount FROM budgets WHERE month=?", (month,)).fetchone()
    if row:
        budget = row["amount"]
        spent = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE date LIKE ?",
            (f"{month}%",)
        ).fetchone()["s"]
        pct = spent / budget * 100
        print()
        if pct >= 100:
            print(c(C.BG_RED + C.WHITE, f"  BUDGET EXCEEDED! Spent Rs.{spent:,.2f} of Rs.{budget:,.2f} ({pct:.0f}%)"))
        elif pct >= 80:
            warn(f"Budget alert! Used {pct:.0f}% of Rs.{budget:,.2f} this month.")
        elif pct >= 60:
            info(f"Budget check: {pct:.0f}% used this month.")

    conn.close()
    print()
    success(f"Added '{desc}' — {format_amount(amount)} [{category}] on {exp_date}")
    input(c(C.GRAY, "\n  Press Enter to continue..."))


def delete_expense():
    clear(); banner()
    print(c(C.BOLD, "\n  Delete Expense\n"))
    divider()

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC LIMIT 20"
    ).fetchall()

    if not rows:
        error("No expenses found.")
        conn.close()
        input(c(C.GRAY, "\n  Press Enter to continue...")); return

    print(c(C.BOLD, f"\n  {'ID':<5} {'Date':<12} {'Category':<14} {'Amount':>12}  Description"))
    divider()
    for r in rows:
        print(f"  {c(C.CYAN, str(r['id'])):<14} {r['date']:<12} {r['category']:<14} "
              f"{c(C.GREEN, 'Rs.{0:,.2f}'.format(r['amount'])):>20}  {r['description']}")

    print()
    try:
        eid = int(input(c(C.YELLOW, "  Enter ID to delete (0 to cancel): ")))
        if eid == 0:
            conn.close(); return
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
        if not row:
            error("ID not found.")
        else:
            confirm = input(c(C.RED, f"  Delete '{row['description']}' Rs.{row['amount']:,.2f}? (y/n): "))
            if confirm.lower() == "y":
                conn.execute("DELETE FROM expenses WHERE id=?", (eid,))
                conn.commit()
                success("Expense deleted.")
            else:
                info("Cancelled.")
    except ValueError:
        error("Invalid ID.")

    conn.close()
    input(c(C.GRAY, "\n  Press Enter to continue..."))


def view_summary():
    clear(); banner()
    print(c(C.BOLD, "\n  Monthly Summary\n"))
    divider()

    month = get_month()
    conn = get_db()

    total = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE date LIKE ?",
        (f"{month}%",)
    ).fetchone()["s"]

    cats = conn.execute(
        """SELECT category, SUM(amount) as total, COUNT(*) as cnt
           FROM expenses WHERE date LIKE ?
           GROUP BY category ORDER BY total DESC""",
        (f"{month}%",)
    ).fetchall()

    budget_row = conn.execute(
        "SELECT amount FROM budgets WHERE month=?", (month,)
    ).fetchone()
    budget = budget_row["amount"] if budget_row else None

    count = conn.execute(
        "SELECT COUNT(*) as c FROM expenses WHERE date LIKE ?",
        (f"{month}%",)
    ).fetchone()["c"]
    conn.close()

    print(c(C.BOLD, f"\n  {month}"))
    divider()
    print(f"  Total spent  : {format_amount(total)}")
    print(f"  Transactions : {c(C.WHITE, str(count))}")

    if budget:
        remaining = budget - total
        color = C.GREEN if remaining >= 0 else C.RED
        print(f"  Budget       : {format_amount(budget)}")
        print(f"  Remaining    : {c(color, f'Rs.{remaining:,.2f}')}")
        print(f"  {spend_bar(total, budget)}")

    if cats:
        print(c(C.BOLD, "\n  Breakdown by category:\n"))
        print(c(C.GRAY, f"  {'Category':<16} {'Spent':>12}  {'Txns':>5}  {'Share':>6}"))
        divider()
        for cat in cats:
            pct = cat["total"] / total * 100 if total > 0 else 0
            print(f"  {cat['category']:<16} "
                  f"{c(C.GREEN, 'Rs.{0:,.2f}'.format(cat['total'])):>20}  "
                  f"{c(C.CYAN, str(cat['cnt'])):>13}  "
                  f"{c(C.YELLOW, f'{pct:.1f}%'):>14}")
    else:
        warn("No expenses found for this month.")

    input(c(C.GRAY, "\n  Press Enter to continue..."))


def filter_expenses():
    clear(); banner()
    print(c(C.BOLD, "\n  Filter Expenses\n"))
    divider()

    print(f"    {c(C.CYAN,'1')}. By category")
    print(f"    {c(C.CYAN,'2')}. By date range")
    print(f"    {c(C.CYAN,'3')}. By month")
    print(f"    {c(C.CYAN,'4')}. Back")

    choice = input(c(C.YELLOW, "\n  Choice: ")).strip()
    conn = get_db()
    rows = []
    label = ""

    if choice == "1":
        category = pick_category()
        rows = conn.execute(
            "SELECT * FROM expenses WHERE category=? ORDER BY date DESC",
            (category,)
        ).fetchall()
        label = f"Category: {category}"

    elif choice == "2":
        start = input(c(C.YELLOW, "  Start date (YYYY-MM-DD): ")).strip()
        end   = input(c(C.YELLOW, "  End date   (YYYY-MM-DD): ")).strip()
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
            rows = conn.execute(
                "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                (start, end)
            ).fetchall()
            label = f"{start} to {end}"
        except ValueError:
            error("Invalid date format.")
            conn.close()
            input(c(C.GRAY, "\n  Press Enter to continue...")); return

    elif choice == "3":
        month = get_month()
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC",
            (f"{month}%",)
        ).fetchall()
        label = f"Month: {month}"

    else:
        conn.close(); return

    conn.close()
    print(c(C.BOLD, f"\n  Results — {label}\n"))

    if not rows:
        warn("No expenses found.")
    else:
        total = 0
        print(c(C.GRAY, f"  {'ID':<5} {'Date':<12} {'Category':<14} {'Amount':>12}  Description"))
        divider()
        for r in rows:
            total += r["amount"]
            print(f"  {c(C.CYAN,str(r['id'])):<14} {r['date']:<12} {r['category']:<14} "
                  f"{c(C.GREEN, 'Rs.{0:,.2f}'.format(r['amount'])):>20}  {r['description']}")
        divider()
        print(f"  {'TOTAL':>46} {format_amount(total)}")
        print(c(C.GRAY, f"\n  {len(rows)} expense(s) found"))

    input(c(C.GRAY, "\n  Press Enter to continue..."))


def set_budget():
    clear(); banner()
    print(c(C.BOLD, "\n  Set Monthly Budget\n"))
    divider()

    month = get_month()
    conn = get_db()
    existing = conn.execute(
        "SELECT amount FROM budgets WHERE month=?", (month,)
    ).fetchone()

    if existing:
        info(f"Current budget for {month}: {format_amount(existing['amount'])}")

    while True:
        try:
            amount = float(input(c(C.YELLOW, f"  New budget for {month} (Rs.): ")))
            if amount <= 0: raise ValueError
            break
        except ValueError:
            error("Enter a valid positive amount.")

    conn.execute(
        "INSERT INTO budgets (month, amount) VALUES (?, ?) "
        "ON CONFLICT(month) DO UPDATE SET amount=excluded.amount",
        (month, amount)
    )
    conn.commit()

    spent = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE date LIKE ?",
        (f"{month}%",)
    ).fetchone()["s"]
    conn.close()

    print()
    success(f"Budget set to {format_amount(amount)} for {month}")
    print(f"\n  Already spent : {format_amount(spent)}")
    print(f"  Remaining     : {format_amount(amount - spent)}")
    print(f"  {spend_bar(spent, amount)}")
    input(c(C.GRAY, "\n  Press Enter to continue..."))


def export_csv():
    clear(); banner()
    print(c(C.BOLD, "\n  Export to CSV\n"))
    divider()

    print(f"    {c(C.CYAN,'1')}. Export specific month")
    print(f"    {c(C.CYAN,'2')}. Export all expenses")
    choice = input(c(C.YELLOW, "\n  Choice: ")).strip()

    conn = get_db()
    if choice == "1":
        month = get_month()
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date LIKE ? ORDER BY date",
            (f"{month}%",)
        ).fetchall()
        filename = f"expenses_{month}.csv"
    else:
        rows = conn.execute(
            "SELECT * FROM expenses ORDER BY date"
        ).fetchall()
        filename = "expenses_all.csv"
    conn.close()

    if not rows:
        warn("No expenses found to export.")
        input(c(C.GRAY, "\n  Press Enter to continue...")); return

    filepath = Path.cwd() / filename
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Date", "Category", "Amount (Rs.)", "Description", "Created At"])
        for r in rows:
            writer.writerow([r["id"], r["date"], r["category"],
                             r["amount"], r["description"], r["created_at"]])

    print()
    success(f"Exported {len(rows)} expenses to:")
    print(c(C.CYAN, f"  {filepath}"))
    input(c(C.GRAY, "\n  Press Enter to continue..."))


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu():
    init_db()
    while True:
        clear(); banner()

        conn = get_db()
        month = date.today().strftime("%Y-%m")
        today_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE date=?",
            (date.today().isoformat(),)
        ).fetchone()["s"]
        month_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE date LIKE ?",
            (f"{month}%",)
        ).fetchone()["s"]
        budget_row = conn.execute(
            "SELECT amount FROM budgets WHERE month=?", (month,)
        ).fetchone()
        conn.close()

        print(c(C.GRAY, f"\n  Today: {date.today().strftime('%d %b %Y')}"))
        print(f"  Today's spend  : {format_amount(today_total)}")
        print(f"  This month     : {format_amount(month_total)}", end="")
        if budget_row:
            pct = month_total / budget_row["amount"] * 100
            color = C.GREEN if pct < 70 else C.YELLOW if pct < 90 else C.RED
            print(f"  {c(color, f'({pct:.0f}% of budget)')}", end="")
        print("\n")

        divider()
        print(c(C.BOLD, "\n  What would you like to do?\n"))
        options = [
            ("1", "Add expense"),
            ("2", "Delete expense"),
            ("3", "View monthly summary"),
            ("4", "Filter expenses"),
            ("5", "Set monthly budget"),
            ("6", "Export to CSV"),
            ("7", "Exit"),
        ]
        for key, label in options:
            print(f"    {c(C.CYAN, key)}.  {label}")

        print()
        choice = input(c(C.YELLOW, "  Enter choice: ")).strip()

        actions = {
            "1": add_expense,
            "2": delete_expense,
            "3": view_summary,
            "4": filter_expenses,
            "5": set_budget,
            "6": export_csv,
        }

        if choice in actions:
            actions[choice]()
        elif choice == "7":
            print(c(C.CYAN, "\n  Goodbye! Keep tracking those expenses.\n"))
            sys.exit(0)
        else:
            error("Invalid choice. Try again.")


if __name__ == "__main__":
    main_menu()
