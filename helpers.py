"""
WiseBudget AI - Helper functions

Pure data and logic helpers used by the Streamlit app and the AI assistant.
Keeping these out of app.py makes them easy to test and lets the AI module
fall back to the rule-based insights without importing the UI.
"""

import re
import pandas as pd
from pathlib import Path
from datetime import date
from pandas.errors import EmptyDataError


# ============================================================
# File paths and table schemas
# ============================================================

DATA_FOLDER = Path("data")
INCOME_FILE = DATA_FOLDER / "income.csv"
EXPENSES_FILE = DATA_FOLDER / "expenses.csv"
GOALS_FILE = DATA_FOLDER / "goals.csv"
FEEDBACK_FILE = DATA_FOLDER / "feedback.csv"

INCOME_COLUMNS = ["date", "source", "amount"]
EXPENSES_COLUMNS = ["date", "description", "amount", "category"]
GOALS_COLUMNS = ["goal_name", "target_amount", "current_amount", "deadline"]
FEEDBACK_COLUMNS = [
    "date_time",
    "would_use_app",
    "most_useful_feature",
    "preferred_spending_view",
    "what_was_confusing",
    "feature_to_add",
    "design_rating",
    "usefulness_rating",
    "final_comments",
]

EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Bills",
    "Subscriptions",
    "Entertainment",
    "Shopping",
    "Savings",
    "Debt Repayment",
    "Health",
    "Education",
    "Other",
]


# ============================================================
# CSV helpers
# ============================================================

def ensure_csv_exists(file_path, columns):
    """
    Makes sure each CSV file exists.
    If it does not exist, the app creates it with the correct headings.

    Cloud hosting may not allow writing to disk. If the file can't be created,
    that's fine: load_csv falls back to an empty in-memory table with the
    right columns, so the app keeps running with an empty (or missing) data
    folder.
    """
    try:
        DATA_FOLDER.mkdir(exist_ok=True)
        if not file_path.exists():
            empty_table = pd.DataFrame(columns=columns)
            empty_table.to_csv(file_path, index=False)
    except OSError:
        pass


def load_csv(file_path, columns):
    """
    Loads a CSV file.
    If the file is empty or missing, it returns an empty table with the
    expected columns so downstream code can rely on them being present.
    """
    try:
        if file_path.exists():
            data = pd.read_csv(file_path)
            # Guarantee the expected columns exist even if the file was edited.
            for column in columns:
                if column not in data.columns:
                    data[column] = pd.NA
            return data
        return pd.DataFrame(columns=columns)
    except EmptyDataError:
        return pd.DataFrame(columns=columns)


def save_csv(dataframe, file_path):
    """
    Saves data back into a CSV file.
    Returns True on success, False if the disk can't be written to (some
    cloud hosts are read-only), so callers can explain instead of crashing.
    """
    try:
        DATA_FOLDER.mkdir(exist_ok=True)
        dataframe.to_csv(file_path, index=False)
        return True
    except OSError:
        return False


def clean_money_column(dataframe, column_name):
    """
    Converts money columns into numbers.
    Invalid values become 0.
    """
    if column_name in dataframe.columns:
        dataframe[column_name] = pd.to_numeric(
            dataframe[column_name],
            errors="coerce"
        ).fillna(0)

    return dataframe


def ensure_all_csv_files():
    """Create every CSV file with headers if they do not already exist."""
    ensure_csv_exists(INCOME_FILE, INCOME_COLUMNS)
    ensure_csv_exists(EXPENSES_FILE, EXPENSES_COLUMNS)
    ensure_csv_exists(GOALS_FILE, GOALS_COLUMNS)
    ensure_csv_exists(FEEDBACK_FILE, FEEDBACK_COLUMNS)


def save_feedback(feedback_row):
    """
    Append one feedback submission (a dict matching FEEDBACK_COLUMNS)
    to data/feedback.csv, creating the file first if needed.

    Returns True if the row was written to the CSV, False if storage isn't
    available (e.g. read-only cloud hosting). The Feedback page still thanks
    the tester either way - a lost row must never look like a broken form.
    """
    try:
        ensure_csv_exists(FEEDBACK_FILE, FEEDBACK_COLUMNS)
        table = load_csv(FEEDBACK_FILE, FEEDBACK_COLUMNS)
        table = pd.concat([table, pd.DataFrame([feedback_row])], ignore_index=True)
        return save_csv(table, FEEDBACK_FILE)
    except Exception:
        return False


def load_income():
    data = load_csv(INCOME_FILE, INCOME_COLUMNS)
    return clean_money_column(data, "amount")


def load_expenses():
    data = load_csv(EXPENSES_FILE, EXPENSES_COLUMNS)
    return clean_money_column(data, "amount")


def load_goals():
    return load_csv(GOALS_FILE, GOALS_COLUMNS)


def dataframe_to_csv_bytes(dataframe):
    """Encode a dataframe as UTF-8 CSV bytes for a Streamlit download button."""
    return dataframe.to_csv(index=False).encode("utf-8")


def clean_edited_table(edited, key_field, has_category=False):
    """
    Tidy a table coming back from st.data_editor before saving:
      - drop rows with no value in the key field (blank rows the user added)
      - coerce money columns to numbers
      - turn date columns back into YYYY-MM-DD strings (defaulting to today)
    """
    table = edited.copy()

    # Drop blank rows added via the dynamic editor.
    table = table[table[key_field].notna()]
    table = table[table[key_field].astype(str).str.strip() != ""]

    if "amount" in table.columns:
        table = clean_money_column(table, "amount")
    if has_category and "category" in table.columns:
        table["category"] = table["category"].fillna("Other")

    for date_column in ("date", "deadline"):
        if date_column in table.columns:
            parsed = pd.to_datetime(table[date_column], errors="coerce")
            table[date_column] = parsed.dt.strftime("%Y-%m-%d")
            table[date_column] = table[date_column].fillna(date.today().strftime("%Y-%m-%d"))

    return table.reset_index(drop=True)


# ============================================================
# Demo data (used by the app's Demo Mode)
# ============================================================

def get_demo_data():
    """
    Return (income, expenses, goals) DataFrames of realistic but ENTIRELY
    SYNTHETIC UK budgeting data covering the last 6 months, so month filtering,
    trends, saving opportunities and projections can all be demonstrated.

    This is invented example data for a fictional person - it is NOT anyone's
    real bank data, contains no real account details, and is safe to show in a
    public demo. Demo Mode only READS this; the real CSV files are never touched.
    The rows are deterministic (no randomness) so every demo looks the same.

    Some rows use a per-month value of 0.0 to mean "did not happen this month"
    (e.g. an occasional restaurant or train ticket); those are dropped at the
    end, which keeps each month looking a little different.
    """
    today = pd.Timestamp(date.today())
    # Six months of data, oldest to newest.
    months = [today.to_period("M") - offset for offset in range(5, -1, -1)]

    income_rows = []
    expense_rows = []

    for i, month in enumerate(months):
        first_day = month.start_time

        def day(day_number):
            return (first_day + pd.Timedelta(days=day_number - 1)).strftime("%Y-%m-%d")

        # ---- Income: monthly salary, plus occasional freelance ----
        income_rows.append({"date": day(28), "source": "Salary - Meridian Care Ltd", "amount": 2420.00})
        if i in (1, 4):
            income_rows.append({"date": day(15), "source": "Freelance design work", "amount": 185.00})

        # ---- Recurring bills & subscriptions (steady each month) ----
        expense_rows += [
            {"date": day(1),  "description": "Rent - Oakfield Lettings", "amount": 950.00, "category": "Rent"},
            {"date": day(3),  "description": "British Gas energy", "amount": [88.40, 92.10, 79.50, 71.20, 96.80, 90.30][i], "category": "Bills"},
            {"date": day(4),  "description": "Thames Water", "amount": 34.50, "category": "Bills"},
            {"date": day(5),  "description": "EE mobile", "amount": 26.99, "category": "Bills"},
            {"date": day(5),  "description": "BT broadband", "amount": 33.99, "category": "Bills"},
            {"date": day(6),  "description": "Netflix", "amount": 12.99, "category": "Subscriptions"},
            {"date": day(6),  "description": "Spotify", "amount": 11.99, "category": "Subscriptions"},
            {"date": day(7),  "description": "Disney Plus", "amount": 7.99, "category": "Subscriptions"},
            {"date": day(7),  "description": "iCloud storage", "amount": 2.99, "category": "Subscriptions"},
            {"date": day(8),  "description": "PureGym membership", "amount": 24.99, "category": "Health"},
        ]

        # ---- Groceries: several shops a month, amounts vary ----
        expense_rows += [
            {"date": day(2),  "description": "Tesco groceries", "amount": [58.20, 61.40, 54.90, 63.10, 49.80, 57.30][i], "category": "Food"},
            {"date": day(9),  "description": "Aldi shopping", "amount": [37.60, 33.20, 41.10, 29.80, 44.50, 35.70][i], "category": "Food"},
            {"date": day(16), "description": "Sainsburys groceries", "amount": [42.10, 45.80, 38.60, 47.20, 40.30, 43.90][i], "category": "Food"},
            {"date": day(23), "description": "Lidl shopping", "amount": [26.40, 22.90, 30.10, 24.60, 28.70, 21.50][i], "category": "Food"},
        ]

        # ---- Takeaways / eating out ----
        expense_rows += [
            {"date": day(12), "description": "Deliveroo", "amount": [19.50, 24.30, 16.80, 27.40, 21.10, 18.60][i], "category": "Food"},
            {"date": day(25), "description": "Uber Eats", "amount": [22.80, 17.60, 26.40, 19.90, 23.50, 20.20][i], "category": "Food"},
            {"date": day(19), "description": "Nandos", "amount": [0.0, 28.40, 0.0, 31.20, 0.0, 26.80][i], "category": "Food"},
        ]

        # ---- Transport ----
        expense_rows += [
            {"date": day(2),  "description": "TfL travel", "amount": [78.00, 82.50, 74.00, 88.00, 71.50, 80.00][i], "category": "Transport"},
            {"date": day(17), "description": "Trainline ticket", "amount": [0.0, 34.80, 0.0, 0.0, 42.30, 0.0][i], "category": "Transport"},
            {"date": day(21), "description": "Uber", "amount": [14.20, 0.0, 18.60, 11.40, 0.0, 16.90][i], "category": "Transport"},
        ]

        # ---- Shopping / entertainment / health ----
        expense_rows += [
            {"date": day(14), "description": "Amazon order", "amount": [31.50, 47.99, 22.40, 55.20, 18.90, 39.60][i], "category": "Shopping"},
            {"date": day(18), "description": "ASOS clothes", "amount": [0.0, 0.0, 48.00, 0.0, 62.50, 0.0][i], "category": "Shopping"},
            {"date": day(20), "description": "Cineworld tickets", "amount": [0.0, 25.00, 0.0, 25.00, 0.0, 25.00][i], "category": "Entertainment"},
            {"date": day(27), "description": "The Crown pub", "amount": [24.60, 31.80, 19.40, 28.70, 22.10, 26.30][i], "category": "Entertainment"},
            {"date": day(11), "description": "Boots pharmacy", "amount": [0.0, 12.80, 0.0, 9.40, 0.0, 14.20][i], "category": "Health"},
        ]

        # ---- Debt & savings ----
        expense_rows += [
            {"date": day(26), "description": "Capital One credit card", "amount": 65.00, "category": "Debt Repayment"},
            {"date": day(10), "description": "Klarna payment", "amount": [0.0, 30.00, 30.00, 0.0, 45.00, 30.00][i], "category": "Debt Repayment"},
            {"date": day(28), "description": "Transfer to savings pot", "amount": 250.00, "category": "Savings"},
        ]

    # Drop the "did not happen this month" placeholder rows (amount 0).
    expense_rows = [row for row in expense_rows if row["amount"] > 0]

    income = pd.DataFrame(income_rows, columns=INCOME_COLUMNS)
    expenses = pd.DataFrame(expense_rows, columns=EXPENSES_COLUMNS)

    goals = pd.DataFrame(
        [
            {
                "goal_name": "Emergency Fund",
                "target_amount": 3000.0,
                "current_amount": 1500.0,
                "deadline": (today + pd.Timedelta(days=180)).strftime("%Y-%m-%d"),
            },
            {
                "goal_name": "Holiday to Spain",
                "target_amount": 1500.0,
                "current_amount": 620.0,
                "deadline": (today + pd.Timedelta(days=300)).strftime("%Y-%m-%d"),
            },
            {
                "goal_name": "New Laptop",
                "target_amount": 900.0,
                "current_amount": 300.0,
                "deadline": (today + pd.Timedelta(days=120)).strftime("%Y-%m-%d"),
            },
        ],
        columns=GOALS_COLUMNS,
    )

    return income, expenses, goals


# ============================================================
# Date filtering
# ============================================================

ALL_TIME = "All time"


def format_month_label(month):
    """
    Turn a "YYYY-MM" period string into a friendly label like "July 2026".
    Leaves "All time" (and anything unparseable) unchanged. Used so the UI can
    show readable month names while the underlying value stays "YYYY-MM" for
    filtering.
    """
    if month == ALL_TIME:
        return month
    try:
        return pd.to_datetime(str(month), format="%Y-%m").strftime("%B %Y")
    except (ValueError, TypeError):
        return str(month)


def get_month_options(*dataframes):
    """
    Return a list of month strings (YYYY-MM) found across the given tables,
    most recent first, with an "All time" option at the front.
    """
    months = set()
    for dataframe in dataframes:
        if "date" in dataframe.columns:
            parsed = pd.to_datetime(dataframe["date"], errors="coerce")
            for stamp in parsed.dropna():
                months.add(stamp.strftime("%Y-%m"))

    ordered = sorted(months, reverse=True)
    return [ALL_TIME] + ordered


def filter_by_month(dataframe, month):
    """
    Keep only rows whose date falls within the chosen month (YYYY-MM).
    Passing "All time" returns the table unchanged.
    """
    if month == ALL_TIME or "date" not in dataframe.columns or dataframe.empty:
        return dataframe

    parsed = pd.to_datetime(dataframe["date"], errors="coerce")
    mask = parsed.dt.strftime("%Y-%m") == month
    return dataframe[mask].reset_index(drop=True)


def count_months_covered(expenses_data):
    """
    How many distinct months (YYYY-MM) appear in the expense dates.
    Used to turn an "All time" total into an honest monthly average.
    Always returns at least 1 so division is safe.
    """
    if expenses_data is None or expenses_data.empty or "date" not in expenses_data.columns:
        return 1
    parsed = pd.to_datetime(expenses_data["date"], errors="coerce").dropna()
    if parsed.empty:
        return 1
    return max(1, parsed.dt.strftime("%Y-%m").nunique())


# ============================================================
# Categorisation (simple rule-based AI classifier)
# ============================================================

def auto_categorise_expense(description):
    """
    Automatically detects the category of an expense based on keywords.
    This is a simple rule-based classifier used when the user picks
    "Auto Detect" instead of choosing a category by hand.
    """
    text = str(description).lower()

    keyword_map = {
        # Food is checked before Shopping (dict order) so supermarket trips like
        # "Aldi Shopping" map to Food, not Shopping.
        "Food": [
            "tesco", "aldi", "lidl", "asda", "sainsbury", "morrisons",
            "restaurant", "food", "groceries", "supermarket", "food shop",
            "food shopping", "takeaway", "uber eats",
            "deliveroo", "just eat", "mcdonald", "kfc", "burger", "coffee"
        ],
        "Transport": [
            "uber", "bolt", "train", "bus", "tube", "oyster", "tfl",
            "petrol", "fuel", "parking", "taxi", "transport"
        ],
        "Rent": [
            "rent", "landlord", "housing", "room"
        ],
        "Bills": [
            "electric", "gas", "water", "council tax", "wifi", "internet",
            "phone bill", "ee", "vodafone", "three", "o2", "utility"
        ],
        "Subscriptions": [
            "netflix", "spotify", "amazon prime", "prime", "disney",
            "youtube premium", "icloud", "subscription", "membership"
        ],
        "Entertainment": [
            "cinema", "movie", "club", "bar", "pub", "drinks",
            "concert", "game", "entertainment"
        ],
        "Shopping": [
            "amazon", "zara", "nike", "jd", "clothes", "shopping",
            "primark", "shein", "asos"
        ],
        "Savings": [
            "saving", "savings", "emergency fund", "investment", "invest"
        ],
        "Debt Repayment": [
            "loan", "credit card", "debt", "repayment", "klarna",
            "paypal credit"
        ],
        "Health": [
            "gym", "doctor", "dentist", "pharmacy", "medicine",
            "health", "fitness"
        ],
        "Education": [
            "course", "book", "university", "college", "tuition",
            "education", "training"
        ]
    }

    for category, keywords in keyword_map.items():
        for keyword in keywords:
            # Whole-word match (see _contains_keyword) so a keyword can't trip
            # on a substring - e.g. "tfl" must not match inside "netflix".
            if _contains_keyword(text, keyword):
                return category

    return "Other"


# ============================================================
# Budget maths
# ============================================================

def compute_summary(income_data, expenses_data):
    """
    Return the headline budget figures as a dictionary.
    Savings (money deliberately set aside) is treated as kept money rather
    than spending, so it is excluded from "living expenses" and the savings
    rate reflects everything not spent on living costs.
    """
    income_data = clean_money_column(income_data.copy(), "amount")
    expenses_data = clean_money_column(expenses_data.copy(), "amount")

    total_income = float(income_data["amount"].sum()) if not income_data.empty else 0.0
    total_expenses = float(expenses_data["amount"].sum()) if not expenses_data.empty else 0.0

    if not expenses_data.empty and "category" in expenses_data.columns:
        deliberate_savings = float(
            expenses_data.loc[expenses_data["category"] == "Savings", "amount"].sum()
        )
    else:
        deliberate_savings = 0.0

    living_expenses = total_expenses - deliberate_savings
    remaining_balance = total_income - total_expenses

    if total_income > 0:
        savings_rate = ((total_income - living_expenses) / total_income) * 100
    else:
        savings_rate = 0.0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "living_expenses": living_expenses,
        "deliberate_savings": deliberate_savings,
        "remaining_balance": remaining_balance,
        "savings_rate": savings_rate,
    }


def monthly_totals(income_data, expenses_data):
    """
    Return a DataFrame indexed by month (YYYY-MM) with Income and Expenses
    columns, sorted oldest to newest. Handy for a trend chart.
    """
    def by_month(dataframe):
        if dataframe.empty or "date" not in dataframe.columns:
            return pd.Series(dtype="float64")
        cleaned = clean_money_column(dataframe.copy(), "amount")
        months = pd.to_datetime(cleaned["date"], errors="coerce").dt.strftime("%Y-%m")
        return cleaned.groupby(months)["amount"].sum()

    result = pd.DataFrame(
        {
            "Income": by_month(income_data),
            "Expenses": by_month(expenses_data),
        }
    ).fillna(0.0)

    return result.sort_index()


def category_totals(expenses_data):
    """Return a Series of total spend per category, largest first."""
    expenses_data = clean_money_column(expenses_data.copy(), "amount")
    if expenses_data.empty or "category" not in expenses_data.columns:
        return pd.Series(dtype="float64")

    return (
        expenses_data
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )


# ============================================================
# Savings goals
# ============================================================

def prepare_goals_data(goals_data):
    """
    Adds savings goal calculations: remaining amount, progress %, and whether
    the deadline has passed.
    """
    if goals_data.empty:
        return goals_data

    goals_data = goals_data.copy()
    goals_data = clean_money_column(goals_data, "target_amount")
    goals_data = clean_money_column(goals_data, "current_amount")

    goals_data["remaining_amount"] = (
        goals_data["target_amount"] - goals_data["current_amount"]
    ).clip(lower=0)

    goals_data["progress_percentage"] = goals_data.apply(
        lambda row: (row["current_amount"] / row["target_amount"]) * 100
        if row["target_amount"] > 0 else 0,
        axis=1
    )

    goals_data["progress_percentage"] = goals_data["progress_percentage"].clip(
        lower=0,
        upper=100
    )

    today = pd.Timestamp(date.today())
    deadlines = pd.to_datetime(goals_data.get("deadline"), errors="coerce")
    goals_data["is_overdue"] = (
        deadlines.notna()
        & (deadlines < today)
        & (goals_data["progress_percentage"] < 100)
    )

    return goals_data


# ============================================================
# Rule-based budget insights (fallback when AI is unavailable)
# ============================================================

def generate_budget_insights(
    total_income,
    total_expenses,
    remaining_balance,
    savings_rate,
    expenses_data
):
    """
    Generates budgeting insights using simple rules.
    Used directly when the local AI is unavailable, and as background context
    the AI assistant can build on when it is running.
    """
    insights = []

    if total_income <= 0:
        insights.append(
            (
                "warning",
                "No income has been recorded yet. Add your income first so WiseBudget AI can analyse your budget properly."
            )
        )
        return insights

    if total_expenses <= 0:
        insights.append(
            (
                "info",
                "No expenses have been recorded yet. Add expenses so WiseBudget AI can identify your spending habits."
            )
        )
        return insights

    if remaining_balance < 0:
        insights.append(
            (
                "error",
                "You are spending more than your income. This is a serious budgeting issue. Reduce non-essential expenses immediately."
            )
        )
    elif savings_rate >= 20:
        insights.append(
            (
                "success",
                "Your savings rate is strong. Saving 20% or more of your income is a good financial habit."
            )
        )
    elif savings_rate >= 10:
        insights.append(
            (
                "info",
                "Your savings rate is acceptable, but there is room to improve. Aim for at least 15% if possible."
            )
        )
    else:
        insights.append(
            (
                "warning",
                "Your savings rate is below 10%. Try reducing flexible spending and setting a clear savings target."
            )
        )

    totals = category_totals(expenses_data)

    if not totals.empty:
        biggest_category = totals.index[0]
        biggest_amount = totals.iloc[0]
        biggest_percentage = (biggest_amount / total_income) * 100

        insights.append(
            (
                "info",
                f"Your biggest spending category is {biggest_category}, with £{biggest_amount:,.2f} spent. "
                f"This represents {biggest_percentage:.1f}% of your income."
            )
        )

        food_spending = totals.get("Food", 0)
        subscriptions_spending = totals.get("Subscriptions", 0)
        entertainment_spending = totals.get("Entertainment", 0)
        shopping_spending = totals.get("Shopping", 0)
        debt_spending = totals.get("Debt Repayment", 0)

        if food_spending > total_income * 0.25:
            insights.append(
                (
                    "warning",
                    "Food spending is above 25% of your income. Consider setting a weekly food budget and reducing takeaways."
                )
            )

        if subscriptions_spending > 50:
            insights.append(
                (
                    "warning",
                    "Subscription spending is above £50. Review unused subscriptions and cancel anything you do not need."
                )
            )

        if entertainment_spending > total_income * 0.15:
            insights.append(
                (
                    "warning",
                    "Entertainment spending is high compared to your income. Set a monthly entertainment limit."
                )
            )

        if shopping_spending > total_income * 0.15:
            insights.append(
                (
                    "warning",
                    "Shopping spending is high. Separate needs from wants before making purchases."
                )
            )

        if debt_spending > 0:
            insights.append(
                (
                    "info",
                    "You have recorded debt repayment. Prioritising high-interest debt can improve your financial stability."
                )
            )

    if remaining_balance > 0:
        suggested_saving = remaining_balance * 0.50

        insights.append(
            (
                "success",
                f"You have £{remaining_balance:,.2f} remaining. One possible action is to save or invest part of it. "
                f"For example, saving 50% of the remaining balance would be £{suggested_saving:,.2f}."
            )
        )

    return insights


# ============================================================
# Smart Saving Opportunities (rule-based bill / spending review)
# ============================================================
#
# Each rule below describes one type of recurring cost we can spot from the
# expense list. It holds the keywords/categories that hint at it, a broad
# ESTIMATED saving range, why it matters, and concrete, non-advice actions.
#
# Important safety rules baked into this design:
#   - The percentages are deliberately wide ESTIMATES, never guarantees.
#   - We never tell the user to switch to a named provider, and never claim a
#     specific provider/product is definitely cheaper.
#   - Actions only ever say things like "compare", "review", "check", "cancel".

SAVING_DISCLAIMER = "This is an estimated saving opportunity, not a guaranteed saving."

SAVING_RULES = [
    {
        "key": "energy",
        "title": "Energy bill detected",
        "category": "Bills",
        "match_categories": [],  # detected by keyword only (Bills is ambiguous)
        "keywords": [
            "gas", "electric", "electricity", "energy", "british gas",
            "octopus", "edf", "eon", "e.on", "ovo", "shell energy",
            "scottish power", "utility",
        ],
        "saving_low": 5,
        "saving_high": 15,
        "why": (
            "Energy is one of the easiest bills to overpay on, especially on a "
            "standard variable tariff or when bills are based on estimated readings."
        ),
        "actions": [
            "Check whether you are on a standard variable tariff or a fixed deal.",
            "Submit up-to-date meter readings so bills reflect real usage, not estimates.",
            "Review your monthly direct debit so it matches your actual usage.",
            "Compare energy tariffs using official comparison sites or provider websites.",
            "Check your annual usage so you can compare deals like-for-like.",
        ],
    },
    {
        "key": "mobile",
        "title": "Mobile / phone bill detected",
        "category": "Bills",
        "match_categories": [],
        "keywords": [
            "phone", "mobile", "vodafone", "ee", "o2", "three",
            "giffgaff", "lebara", "lyca", "sim",
        ],
        "saving_low": 10,
        "saving_high": 30,
        "why": (
            "Many people keep paying for large allowances, or for a handset, long "
            "after they need to, so a quick review can free up money each month."
        ),
        "actions": [
            "Check whether a cheaper SIM-only plan would cover your needs.",
            "Reduce your data allowance if you rarely use all of it.",
            "Compare networks and current deals before renewing.",
            "If your contract has ended, check you are not still paying for a handset you already own.",
        ],
    },
    {
        "key": "broadband",
        "title": "Broadband / internet bill detected",
        "category": "Bills",
        "match_categories": [],
        "keywords": [
            "broadband", "internet", "wifi", "virgin media", "bt", "sky",
            "talktalk", "plusnet", "vodafone broadband",
        ],
        "saving_low": 10,
        "saving_high": 25,
        "why": (
            "Broadband prices often jump once an introductory deal ends, so "
            "checking your contract can stop you overpaying out of contract."
        ),
        "actions": [
            "Check your contract end date so you know when you can switch penalty-free.",
            "Compare broadband deals using comparison sites or provider websites.",
            "Contact your provider to negotiate your renewal price.",
            "Avoid staying on out-of-contract pricing, which is often higher.",
        ],
    },
    {
        "key": "subscriptions",
        "title": "Subscriptions detected",
        "category": "Subscriptions",
        "match_categories": ["Subscriptions"],
        "keywords": [
            "netflix", "spotify", "disney", "amazon prime", "prime",
            "youtube premium", "icloud", "subscription", "membership",
        ],
        "saving_low": 20,
        "saving_high": 50,
        "why": (
            "Recurring subscriptions are easy to forget and add up quickly, so "
            "cancelling unused ones is one of the simplest ways to save."
        ),
        "actions": [
            "Cancel any subscriptions you no longer use.",
            "Rotate services month to month instead of paying for all at once.",
            "Downgrade to a cheaper plan or an ad-supported tier where it suits you.",
            "Share a family or group plan legally where the service allows it.",
        ],
    },
    {
        "key": "food",
        "title": "Food/Groceries spending detected",
        "category": "Food",
        "match_categories": ["Food"],
        "keywords": [
            "tesco", "aldi", "lidl", "asda", "sainsbury", "morrisons",
            "groceries", "supermarket", "food shop", "food shopping",
            "takeaway", "uber eats", "deliveroo", "just eat",
        ],
        "saving_low": 5,
        "saving_high": 20,
        "why": (
            "Food is a flexible everyday cost, so small changes to shopping and "
            "takeaways can add up to a noticeable monthly saving."
        ),
        "actions": [
            "Set a weekly food budget and try to stick to it.",
            "Reduce takeaways and food-delivery orders.",
            "Compare prices between supermarkets, including cheaper ranges.",
            "Plan meals and batch-cook to cut waste.",
            "Compare branded items against own-brand alternatives.",
        ],
    },
    {
        "key": "transport",
        "title": "Transport spending detected",
        "category": "Transport",
        "match_categories": ["Transport"],
        "keywords": [
            "uber", "bolt", "train", "tube", "tfl", "oyster", "bus",
            "petrol", "fuel", "parking", "taxi",
        ],
        "saving_low": 5,
        "saving_high": 20,
        "why": (
            "Travel costs can often be reduced with the right pass, a railcard, "
            "or a little forward planning."
        ),
        "actions": [
            "Check whether a travelcard or railcard would save you money.",
            "Reduce frequent ride-hailing trips where possible.",
            "Compare weekly and monthly passes against paying per journey.",
            "Plan and book journeys earlier for cheaper fares.",
        ],
    },
    {
        "key": "debt",
        "title": "Potential interest saving opportunity",
        "category": "Debt Repayment",
        "match_categories": ["Debt Repayment"],
        # Debt is not a simple monthly bill saving: any "saving" is a long-term
        # interest reduction that depends on rate and terms. The UI relabels and
        # disclaims it accordingly, and it is excluded from the savings totals.
        "saving_kind": "interest",
        "disclaimer": (
            "Debt savings depend on interest rate, repayment terms, and whether "
            "overpayments are allowed."
        ),
        "keywords": [
            "loan", "credit card", "debt", "repayment", "klarna",
            "paypal credit",
        ],
        "saving_low": 5,
        "saving_high": 15,
        "why": (
            "Reducing high-interest debt lowers the amount you lose to interest, "
            "freeing up money over time. This is general education, not debt advice."
        ),
        "actions": [
            "Prioritise paying off the highest-interest debt first.",
            "Avoid taking on new borrowing while repaying existing debt.",
            "Consider overpayments only where you can comfortably afford them.",
            "Check the interest rate on each debt so you know what it really costs.",
        ],
    },
    {
        "key": "shopping",
        "title": "Shopping spending detected",
        "category": "Shopping",
        "match_categories": ["Shopping"],
        "keywords": [
            "amazon", "zara", "nike", "jd", "clothes", "shein", "asos",
            "shopping",
        ],
        "saving_low": 10,
        "saving_high": 30,
        "why": (
            "Shopping is largely discretionary, so a simple cap and a short pause "
            "before buying can cut impulse spending."
        ),
        "actions": [
            "Use a 48-hour rule before non-essential purchases.",
            "Set a monthly shopping cap and track against it.",
            "Separate needs from wants before buying.",
            "Check return and refund options on recent purchases.",
        ],
    },
    {
        "key": "entertainment",
        "title": "Entertainment spending detected",
        "category": "Entertainment",
        "match_categories": ["Entertainment"],
        "keywords": [
            "cinema", "movie", "bar", "pub", "club", "drinks", "concert",
            "game",
        ],
        "saving_low": 10,
        "saving_high": 30,
        "why": (
            "Entertainment is enjoyable but flexible, so a budget and cheaper "
            "alternatives can protect your savings without cutting out the fun."
        ),
        "actions": [
            "Set a monthly entertainment budget.",
            "Use cheaper or free alternatives where you can.",
            "Try to avoid impulse spending on nights out.",
        ],
    },
    {
        "key": "gym_health",
        "title": "Gym / health spending detected",
        "category": "Health",
        "match_categories": ["Health"],
        "keywords": [
            "gym", "fitness", "puregym", "the gym group", "david lloyd",
            "pharmacy",
        ],
        "saving_low": 10,
        "saving_high": 40,
        "why": (
            "Memberships are great value when used, but an unused or rarely-used "
            "membership is an easy saving to spot."
        ),
        "actions": [
            "Check whether you use your membership often enough to justify the cost.",
            "Compare cheaper gyms or off-peak memberships.",
            "Pause or cancel a membership you are not currently using.",
        ],
    },
    {
        "key": "education",
        "title": "Education spending detected",
        "category": "Education",
        "match_categories": ["Education"],
        "keywords": [
            "course", "book", "university", "college", "udemy", "coursera",
            "training",
        ],
        "saving_low": 10,
        "saving_high": 30,
        "why": (
            "Learning is valuable, but free resources and finishing what you start "
            "can prevent money going to waste."
        ),
        "actions": [
            "Use free learning resources before paying for courses.",
            "Check whether student or other discounts apply.",
            "Avoid buying new courses before finishing the ones you already have.",
        ],
    },
]

# A short, concrete "how you'd actually get this saving" phrase per rule, so the
# estimate never feels like a number out of nowhere. It names the main lever(s)
# (e.g. a railcard, a cheaper tariff) - the fuller checklist is in each rule's
# "actions". Deliberately generic (no named provider, no invented price).
SAVING_HOW = {
    "energy": "comparing energy tariffs and moving to a cheaper or fixed plan, "
              "with up-to-date meter readings",
    "mobile": "switching to a cheaper SIM-only deal that matches how much data "
              "you actually use",
    "broadband": "haggling your renewal price or switching when your contract "
                 "ends, instead of rolling onto out-of-contract pricing",
    "subscriptions": "cancelling or downgrading services you rarely use, or "
                     "rotating them month to month",
    "food": "planning meals, cutting takeaways and food delivery, and comparing "
            "own-brand ranges between supermarkets",
    "transport": "using a railcard or travelcard, and cutting frequent "
                 "ride-hailing where you can",
    "debt": "putting any spare money toward the highest-interest balance first "
            "so less is lost to interest over time",
    "shopping": "setting a monthly cap and giving yourself a 48-hour pause "
                "before non-essential buys",
    "entertainment": "setting a monthly limit and swapping some paid nights out "
                     "for cheaper or free options",
    "gym_health": "switching to a cheaper or off-peak gym, or pausing a "
                  "membership you are not really using",
    "education": "using free learning resources first and claiming any student "
                 "or other discounts",
}

# Quick lookup by rule key (e.g. to give Food priority over Shopping below).
_SAVING_RULES_BY_KEY = {rule["key"]: rule for rule in SAVING_RULES}


def _contains_keyword(text, keyword):
    """
    True if `keyword` appears in `text` as a whole word, allowing a simple
    trailing "s" plural (so "sainsbury" still matches "sainsburys").

    Word boundaries stop false matches in the MIDDLE of a word - for example
    "tfl" inside "ne[tfl]ix", "gas" inside "Ve[gas]", or "ee" inside "coff[ee]"
    - which a plain substring check would wrongly catch.
    """
    pattern = r"\b" + re.escape(keyword) + r"s?\b"
    return re.search(pattern, text) is not None


def _format_detected_from(descriptions, limit=4):
    """Turn the triggering expense descriptions into a short, readable string."""
    if not descriptions:
        return "Recurring spending"
    if len(descriptions) <= limit:
        return ", ".join(descriptions)
    shown = ", ".join(descriptions[:limit])
    return f"{shown}, and {len(descriptions) - limit} more"


def generate_saving_opportunities(expenses_data, income_data=None, months_covered=1):
    """
    Scan recorded expenses and highlight where the user *might* be able to save
    money (energy, mobile, broadband, subscriptions, food, transport, etc.).

    Returns a list of dictionaries, one per detected cost type. Each expense is
    counted towards at most one opportunity (the most specific keyword wins),
    and several expenses of the same type are combined into a single
    opportunity using their total amount.

    `months_covered` (default 1) divides each combined amount so that multi-
    month data (e.g. "All time") is analysed as an honest MONTHLY AVERAGE
    instead of being treated like one month's spending. Pass the result of
    count_months_covered() when analysing more than one month.

    The savings shown are broad ESTIMATES (a low-high range), never guarantees,
    and we never claim a specific provider is cheaper. `income_data` is accepted
    for future use and so callers can pass it without breaking.
    """
    # Nothing recorded yet -> nothing to analyse.
    if expenses_data is None or expenses_data.empty:
        return []

    expenses_data = clean_money_column(expenses_data.copy(), "amount")

    # For each rule key, accumulate the total amount and the descriptions that
    # triggered it (so the card can show "detected from ...").
    buckets = {}

    for _, row in expenses_data.iterrows():
        description = str(row.get("description", "")).strip()
        category = str(row.get("category", "")).strip()
        amount = float(row.get("amount", 0) or 0)
        text = description.lower()

        # 1) Prefer the most specific keyword match (longest keyword wins), so
        #    "uber eats" maps to Food rather than "uber" mapping to Transport.
        matched_rule = None
        best_length = -1
        for rule in SAVING_RULES:
            for keyword in rule["keywords"]:
                if len(keyword) > best_length and _contains_keyword(text, keyword):
                    matched_rule = rule
                    best_length = len(keyword)

        # 1b) Food/Groceries always beats Shopping. The generic word "shopping"
        #     is longer than e.g. "aldi", so without this a supermarket trip like
        #     "Aldi Shopping" would be mislabelled as Shopping. If the best match
        #     is Shopping but a Food keyword is present, treat it as Food.
        if matched_rule is not None and matched_rule["key"] == "shopping":
            food_rule = _SAVING_RULES_BY_KEY["food"]
            if any(_contains_keyword(text, kw) for kw in food_rule["keywords"]):
                matched_rule = food_rule

        # 2) If no keyword matched, fall back to the expense's own category.
        if matched_rule is None:
            for rule in SAVING_RULES:
                if category in rule["match_categories"]:
                    matched_rule = rule
                    break

        # No saving rule applies to this expense -> skip it.
        if matched_rule is None:
            continue

        bucket = buckets.setdefault(
            matched_rule["key"],
            {"amount": 0.0, "descriptions": []},
        )
        bucket["amount"] += amount
        if description and description not in bucket["descriptions"]:
            bucket["descriptions"].append(description)

    # Build one opportunity dictionary per triggered rule.
    months_covered = max(1, int(months_covered))
    opportunities = []
    for rule in SAVING_RULES:
        bucket = buckets.get(rule["key"])
        if not bucket or bucket["amount"] <= 0:
            continue

        # Average per month, so multi-month data gives honest monthly figures.
        current_amount = round(bucket["amount"] / months_covered, 2)
        monthly_low = round(current_amount * rule["saving_low"] / 100, 2)
        monthly_high = round(current_amount * rule["saving_high"] / 100, 2)
        yearly_low = round(monthly_low * 12, 2)
        yearly_high = round(monthly_high * 12, 2)

        # Priority is based on the best-case yearly saving.
        if yearly_high >= 150:
            priority = "High"
        elif yearly_high >= 50:
            priority = "Medium"
        else:
            priority = "Low"

        opportunities.append({
            "title": rule["title"],
            "category": rule["category"],
            "detected_from": _format_detected_from(bucket["descriptions"]),
            "current_amount": current_amount,
            "saving_percentage_low": rule["saving_low"],
            "saving_percentage_high": rule["saving_high"],
            "estimated_monthly_saving_low": monthly_low,
            "estimated_monthly_saving_high": monthly_high,
            "estimated_yearly_saving_low": yearly_low,
            "estimated_yearly_saving_high": yearly_high,
            "priority": priority,
            "why_it_matters": rule["why"],
            "action_steps": list(rule["actions"]),
            # "saving" for normal bills/spending, "interest" for debt repayment
            # (shown and totalled differently by the UI).
            "saving_kind": rule.get("saving_kind", "saving"),
            "disclaimer": rule.get("disclaimer", SAVING_DISCLAIMER),
            # A concrete "how you'd get this saving" phrase for the UI.
            "how_to_save": SAVING_HOW.get(rule["key"], "following the steps below"),
        })

    # Surface the biggest, most important opportunities first.
    priority_rank = {"High": 0, "Medium": 1, "Low": 2}
    opportunities.sort(
        key=lambda opp: (
            priority_rank[opp["priority"]],
            -opp["estimated_yearly_saving_high"],
        )
    )
    return opportunities


def summarise_saving_opportunities(opportunities):
    """
    Totals for the summary box shown above the opportunity cards.

    Debt repayment ("interest"-kind) opportunities are EXCLUDED from the saving
    totals: a debt "saving" is a long-term interest reduction that depends on
    the interest rate/APR and repayment terms, which the app does not have, so
    it cannot be summed like a straightforward bill saving.
    """
    total_monthly_low = total_monthly_high = 0.0
    total_yearly_low = total_yearly_high = 0.0
    counted = 0

    for opp in opportunities:
        if opp.get("saving_kind") == "interest":
            continue  # exclude debt from the totals (no interest-rate data)
        total_monthly_low += opp["estimated_monthly_saving_low"]
        total_monthly_high += opp["estimated_monthly_saving_high"]
        total_yearly_low += opp["estimated_yearly_saving_low"]
        total_yearly_high += opp["estimated_yearly_saving_high"]
        counted += 1

    return {
        "count": len(opportunities),
        "saving_count": counted,  # opportunities included in the totals
        "total_monthly_low": round(total_monthly_low, 2),
        "total_monthly_high": round(total_monthly_high, 2),
        "total_yearly_low": round(total_yearly_low, 2),
        "total_yearly_high": round(total_yearly_high, 2),
    }


def top_saving_actions(opportunities, limit=3):
    """
    Pick the top NON-DEBT saving opportunities for the "Your Top 3 Money
    Actions" section. The input list is already sorted by priority then by
    biggest estimated saving, so we just filter and trim.

    Debt is skipped: it is a potential interest reduction, not a simple
    monthly saving, so it is shown separately with its own wording.
    """
    actions = []
    for opp in opportunities:
        if opp.get("saving_kind") == "interest":
            continue

        # Shorten "Mobile / phone bill detected" -> "Mobile / phone" etc.
        short_title = opp["title"]
        for suffix in (" spending detected", " bill detected", " detected"):
            if short_title.endswith(suffix):
                short_title = short_title[: -len(suffix)]
                break

        actions.append({
            "short_title": short_title,
            "priority": opp["priority"],
            "current_amount": opp["current_amount"],   # what they spend now
            "monthly_low": opp["estimated_monthly_saving_low"],
            "monthly_high": opp["estimated_monthly_saving_high"],
            "next_step": opp["action_steps"][0] if opp["action_steps"] else "Review this cost.",
        })
        if len(actions) == limit:
            break
    return actions


def category_breakdown_table(expenses_data):
    """
    Category totals as a tidy table: Category, Amount, Share % (of total
    spending), largest first. Used by the "Table" spending view.
    """
    totals = category_totals(expenses_data)
    if totals.empty:
        return pd.DataFrame(columns=["Category", "Amount", "Share %"])

    total_spent = float(totals.sum())
    return pd.DataFrame({
        "Category": totals.index,
        "Amount": totals.values,
        "Share %": [
            (amount / total_spent * 100) if total_spent > 0 else 0.0
            for amount in totals.values
        ],
    })


# ============================================================
# Projections (long-term "what if" illustrations)
# ============================================================
#
# These turn a monthly amount into a long-term picture: how a regular saving
# builds up, or what a recurring cost adds up to, over several years.
#
# Important safety design (keeps this within the education-only rules):
#   - With a 0% rate this is STRAIGHT ACCUMULATION - money set aside, no growth.
#   - Any growth rate is one the USER types in (default 0), so the app never
#     invents an interest rate, APR or investment return.
#   - Every result is a simple ILLUSTRATION, not a prediction, guarantee, or
#     personal financial/investment advice. The UI labels it that way.

# Time horizons shown in the projection tables (label, number of months).
PROJECTION_HORIZONS = [
    ("6 months", 6),
    ("1 year", 12),
    ("2 years", 24),
    ("5 years", 60),
    ("10 years", 120),
]


def project_savings(monthly_amount, months, annual_growth_percent=0.0, starting_amount=0.0):
    """
    Illustrate the future value of setting aside `monthly_amount` each month for
    `months` months, starting from `starting_amount`, optionally growing at a
    user-chosen `annual_growth_percent` a year (compounded monthly).

    This is an educational illustration only - NOT a prediction, guarantee, or
    investment advice. With a 0% rate it is simple accumulation (no growth), and
    any rate above 0 is one the user chose, so the app never invents a return.

    Returns a dict:
      months        - horizon in months
      starting      - the starting amount
      contributions - total the person puts in over the period (monthly * months)
      deposits      - starting + contributions (all money actually set aside)
      growth        - the illustrative growth on top (0 when the rate is 0)
      total         - projected total (deposits + growth)
    """
    monthly_amount = max(0.0, float(monthly_amount or 0))
    starting_amount = max(0.0, float(starting_amount or 0))
    months = max(0, int(months))
    monthly_rate = max(0.0, float(annual_growth_percent or 0)) / 100.0 / 12.0

    contributions = monthly_amount * months
    if monthly_rate == 0:
        total = starting_amount + contributions
    else:
        growth_factor = (1 + monthly_rate) ** months
        total = (
            starting_amount * growth_factor
            + monthly_amount * ((growth_factor - 1) / monthly_rate)
        )

    deposits = starting_amount + contributions
    growth = total - deposits

    return {
        "months": months,
        "starting": round(starting_amount, 2),
        "contributions": round(contributions, 2),
        "deposits": round(deposits, 2),
        "growth": round(growth, 2),
        "total": round(total, 2),
    }


def savings_projection_table(monthly_amount, annual_growth_percent=0.0,
                             starting_amount=0.0, horizons=None):
    """
    Run project_savings across each time horizon and return a tidy DataFrame:
    Period, You set aside, Illustrative growth, Projected total.
    """
    horizons = horizons or PROJECTION_HORIZONS
    rows = []
    for label, months in horizons:
        result = project_savings(monthly_amount, months, annual_growth_percent, starting_amount)
        rows.append({
            "Period": label,
            "You set aside": result["deposits"],
            "Illustrative growth": result["growth"],
            "Projected total": result["total"],
        })
    return pd.DataFrame(rows, columns=["Period", "You set aside", "Illustrative growth", "Projected total"])


def expense_cost_table(monthly_amount, horizons=None):
    """
    Show what a recurring cost of `monthly_amount` a month adds up to over time
    (straight accumulation, no growth). Returns a DataFrame: Period, Total cost.
    """
    horizons = horizons or PROJECTION_HORIZONS
    monthly_amount = max(0.0, float(monthly_amount or 0))
    rows = [
        {"Period": label, "Total cost": round(monthly_amount * months, 2)}
        for label, months in horizons
    ]
    return pd.DataFrame(rows, columns=["Period", "Total cost"])
