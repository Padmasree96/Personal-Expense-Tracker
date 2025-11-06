# Step 1 - Import required modules
import csv
import os
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
import textwrap
import sys

# Step 2 - Define constants and CSV structure
CSV_FILE = "expenses.csv"
CSV_FIELDS = ["id", "date", "category", "amount", "description"]
DATE_FORMAT = "%Y-%m-%d"

# Step 3 - Ensure the CSV file exists
def ensure_csv():
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()

# Step 4 - Read all expense records
def read_all():
    ensure_csv()
    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

# Step 5 - Write all records back to CSV
def write_all(rows):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

# Step 6 - Parse amount entered by user
def parse_amount(s):
    try:
        a = Decimal(s)
        return a.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None

# Step 7 - Parse date entered by user
def parse_date(s):
    try:
        dt = datetime.strptime(s, DATE_FORMAT)
        return dt.date()
    except Exception:
        return None

# Step 8 - Format a single expense record for display
def format_row(r):
    return f"{r['id'][:8]} | {r['date']} | {r['category'][:12]:12} | ₹{r['amount']:>8} | {r['description']}"

# Step 9 - Add a new expense entry
def add_expense():
    print("\nAdd a new expense (leave date blank for today).")
    date_in = input(f"Date ({DATE_FORMAT}): ").strip()
    if date_in == "":
        date = datetime.today().date().strftime(DATE_FORMAT)
    else:
        if not parse_date(date_in):
            print("Invalid date format. Use YYYY-MM-DD.")
            return
        date = date_in
    category = input("Category (e.g., food, travel, bills): ").strip() or "misc"
    amount_in = input("Amount (numbers only): ").strip()
    amount = parse_amount(amount_in)
    if amount is None:
        print("Invalid amount.")
        return
    description = input("Short description: ").strip()
    row = {
        "id": str(uuid.uuid4()),
        "date": date,
        "category": category,
        "amount": str(amount),
        "description": description,
    }
    rows = read_all()
    rows.append(row)
    write_all(rows)
    print("Expense added successfully.")

# Step 10 - View all or recent expenses
def view_expenses(limit=None):
    rows = read_all()
    if not rows:
        print("\nNo expenses found.")
        return
    print("\nAll expenses:")
    rows_sorted = sorted(rows, key=lambda r: r["date"], reverse=True)
    count = 0
    for r in rows_sorted:
        print(format_row(r))
        count += 1
        if limit and count >= limit:
            break

# Step 11 - Show summary of expenses by category
def summary_by_category():
    rows = read_all()
    if not rows:
        print("\nNo expenses to summarize.")
        return
    totals = {}
    for r in rows:
        cat = r["category"]
        amt = Decimal(r["amount"])
        totals[cat] = totals.get(cat, Decimal("0.00")) + amt
    print("\nTotal by category:")
    for cat, total in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        print(f"{cat:12} : ₹{total}")

# Step 12 - Show summary by date range
def summary_by_date_range():
    rows = read_all()
    if not rows:
        print("\nNo expenses to summarize.")
        return
    start = input("Start date (YYYY-MM-DD): ").strip()
    end = input("End date (YYYY-MM-DD): ").strip()
    s = parse_date(start)
    e = parse_date(end)
    if not s or not e or s > e:
        print("Invalid date range.")
        return
    total = Decimal("0.00")
    filtered = []
    for r in rows:
        d = parse_date(r["date"])
        if s <= d <= e:
            filtered.append(r)
            total += Decimal(r["amount"])
    if not filtered:
        print("No expenses in that range.")
        return
    print(f"\nExpenses from {start} to {end}:")
    for r in sorted(filtered, key=lambda x: x["date"]):
        print(format_row(r))
    print(f"\nTotal: ₹{total}")

# Step 13 - Edit an existing expense
def edit_expense():
    id_prefix = input("Enter expense id (first 8 chars) to edit: ").strip()
    rows = read_all()
    for idx, r in enumerate(rows):
        if r["id"].startswith(id_prefix):
            print("Current entry:")
            print(format_row(r))
            new_date = input(f"Date [{r['date']}]: ").strip() or r["date"]
            if not parse_date(new_date):
                print("Invalid date.")
                return
            new_cat = input(f"Category [{r['category']}]: ").strip() or r["category"]
            new_amt = input(f"Amount [{r['amount']}]: ").strip() or r["amount"]
            new_amt_parsed = parse_amount(new_amt)
            if new_amt_parsed is None:
                print("Invalid amount.")
                return
            new_desc = input(f"Description [{r['description']}]: ").strip() or r["description"]
            rows[idx].update({
                "date": new_date,
                "category": new_cat,
                "amount": str(new_amt_parsed),
                "description": new_desc
            })
            write_all(rows)
            print("Updated successfully.")
            return
    print("No matching expense found.")

# Step 14 - Delete an expense
def delete_expense():
    id_prefix = input("Enter expense id (first 8 chars) to delete: ").strip()
    rows = read_all()
    matches = [r for r in rows if r["id"].startswith(id_prefix)]
    if not matches:
        print("No matching expense found.")
        return
    print("Found:")
    for r in matches:
        print(format_row(r))
    confirm = input("Type YES to confirm delete: ").strip()
    if confirm == "YES":
        new_rows = [r for r in rows if not r["id"].startswith(id_prefix)]
        write_all(new_rows)
        print("Deleted successfully.")
    else:
        print("Cancelled.")

# Step 15 - Export filtered data to CSV
def export_filtered():
    rows = read_all()
    if not rows:
        print("No data to export.")
        return
    cat = input("Filter by category (leave blank for all): ").strip()
    start = input("Start date (YYYY-MM-DD) leave blank for none: ").strip()
    end = input("End date (YYYY-MM-DD) leave blank for none: ").strip()
    filtered = rows
    if cat:
        filtered = [r for r in filtered if r["category"].lower() == cat.lower()]
    if start:
        s = parse_date(start)
        if not s:
            print("Invalid start date.")
            return
        filtered = [r for r in filtered if parse_date(r["date"]) >= s]
    if end:
        e = parse_date(end)
        if not e:
            print("Invalid end date.")
            return
        filtered = [r for r in filtered if parse_date(r["date"]) <= e]
    if not filtered:
        print("No matching records.")
        return
    out_name = input("Output CSV filename (default export.csv): ").strip() or "export.csv"
    with open(out_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in filtered:
            writer.writerow(r)
    print(f"Exported {len(filtered)} rows to {out_name}.")

# Step 16 - Display main menu
MENU = textwrap.dedent("""
    Personal Expense Tracker
    1) Add expense
    2) View recent expenses
    3) View all expenses
    4) Summary by category
    5) Summary by date range
    6) Edit expense
    7) Delete expense
    8) Export filtered CSV
    9) Quit
""")

# Step 17 - Main program loop
def main():
    ensure_csv()
    while True:
        print(MENU)
        choice = input("Choose an option (1-9): ").strip()
        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses(limit=10)
        elif choice == "3":
            view_expenses()
        elif choice == "4":
            summary_by_category()
        elif choice == "5":
            summary_by_date_range()
        elif choice == "6":
            edit_expense()
        elif choice == "7":
            delete_expense()
        elif choice == "8":
            export_filtered()
        elif choice == "9":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please select between 1-9.")

# Step 18 - Run the program
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)
