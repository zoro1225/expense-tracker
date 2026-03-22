# 💰 SkyCash — CLI Expense Tracker

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=flat&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite&logoColor=white)
![CLI](https://img.shields.io/badge/Interface-CLI-black?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

A fully-featured command-line expense tracker built with Python and SQLite. Track spending, set budgets, filter by category or date, and export reports — all from your terminal.

## Features

- Add & delete expenses with category, date, and description
- Monthly summary with totals and category breakdown
- Filter expenses by category, date range, or month
- Monthly budget alerts — warns at 60%, 80%, and 100% usage
- Export to CSV — specific month or all-time data
- SQLite database — data persists between sessions
- Colored terminal UI — clean, readable interface

## Getting Started

### Prerequisites
- Python 3.7 or higher
- No external libraries needed!

### Run it

```bash
git clone https://github.com/zoro1225/expense-tracker.git
cd expense-tracker
python expense_tracker.py
```

## Project Structure

```
expense-tracker/
├── expense_tracker.py   # Main application
└── README.md
```

The SQLite database is auto-created at `~/.skycash.db` on first run.

## Categories

Food · Transport · Shopping · Entertainment · Health · Bills · Education · Travel · Other

## License

MIT © Shivam Bande
