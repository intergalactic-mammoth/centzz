import enum
import pandas as pd


class FinancialMetric(enum.StrEnum):
    """Financial metrics that can be plotted."""

    BALANCE = "Balance"
    INCOME = "Income"
    EXPENSE = "Expense"
    CUMULATIVE_INCOME = "Cumulative Income"
    CUMULATIVE_EXPENSE = "Cumulative Expense"


class GroupingPeriod(enum.StrEnum):
    """Grouping periods for plotting."""

    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"
    YEAR = "Year"
    NONE = "None"


class GroupBy(enum.StrEnum):
    """Grouping categories for plotting."""

    ACCOUNT = "Account"
    CATEGORY = "Category"
    NONE = "None"


class ChartType(enum.StrEnum):
    PIE = "Pie"
    BAR = "Par"
    LINE = "Line"


GROUPING_PERIOD_TO_PANDAS = {
    GroupingPeriod.DAY: "D",
    GroupingPeriod.WEEK: "W",
    GroupingPeriod.MONTH: "M",
    GroupingPeriod.YEAR: "Y",
    GroupingPeriod.NONE: None,
}


def filter_transactions_by_dates(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Returns a DataFrame with transactions within the given date range."""
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)]
