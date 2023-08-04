"""Utility functions for analytics."""
import enum
import pandas as pd

from Transaction import Transaction


class FinancialMetric(enum.StrEnum):
    """Financial metrics that can be plotted."""

    BALANCE = "Balance"
    INCOME = "Income"
    EXPENSE = "Expense"
    CUMULATIVE_INCOME = "Cumulative Income"
    CUMULATIVE_EXPENSE = "Cumulative Expense"


class TransactionType(enum.StrEnum):
    """Transaction types that can be plotted."""

    # TODO: Does it make sense for Transaction class to
    # also have this as part of it's data model?

    INCOME = "Income"
    EXPENSE = "Expense"
    TRANSFER = "Transfer"
    ALL = "All"


class GroupingPeriod(enum.StrEnum):
    """Grouping periods for plotting."""

    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"
    YEAR = "Year"
    NONE = "None"


class GroupBy(enum.StrEnum):
    """Grouping categories for plotting."""

    NONE = "None"
    CATEGORY = "Category"
    ACCOUNT = "Account"


class ChartType(enum.StrEnum):
    """Chart types for plotting."""

    # PIE = "Pie"
    BAR = "Bar"
    LINE = "Line"


GROUPING_PERIOD_TO_PANDAS = {
    GroupingPeriod.DAY: "D",
    GroupingPeriod.WEEK: "W",
    GroupingPeriod.MONTH: "M",
    GroupingPeriod.YEAR: "Y",
}

GROUPING_PERIOD_TO_ALTAIR_TIMEUNIT = {
    GroupingPeriod.DAY: "yearmonthdate",
    GroupingPeriod.WEEK: "yearweek",
    GroupingPeriod.MONTH: "yearmonth",
    GroupingPeriod.YEAR: "year",
}

FINANCIAL_METRIC_TO_TRANSACTION_FIELD = {
    FinancialMetric.BALANCE: "balance",
    FinancialMetric.INCOME: "credit",
    FinancialMetric.EXPENSE: "debit",
    FinancialMetric.CUMULATIVE_INCOME: "cumulative_credit",
    FinancialMetric.CUMULATIVE_EXPENSE: "cumulative_debit",
}


FINANCIAL_METRIC_TO_TRANSACTION_TYPE = {
    FinancialMetric.BALANCE: TransactionType.ALL,
    FinancialMetric.INCOME: TransactionType.INCOME,
    FinancialMetric.EXPENSE: TransactionType.EXPENSE,
    FinancialMetric.CUMULATIVE_INCOME: TransactionType.INCOME,
    FinancialMetric.CUMULATIVE_EXPENSE: TransactionType.EXPENSE,
}


def filter_df_transactions_by_dates(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Returns a DataFrame with transactions within the given date range."""
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)]


def filter_list_transactions_by_type(
    transactions: list[Transaction], transaction_type: TransactionType
) -> list[Transaction]:
    """Returns a list of transactions of the given type.

    TransactionType.TRANSFER: returns all transfer transactions.
    TransactionType.EXPENSE: returns all expense transactions.
    TransactionType.INCOME: returns all income transactions."""
    if transaction_type == TransactionType.EXPENSE:
        transactions = [
            transaction
            for transaction in transactions
            if transaction.debit > 0 and transaction.category != "Transfer"
        ]
    elif transaction_type == TransactionType.INCOME:
        transactions = [
            transaction
            for transaction in transactions
            if transaction.credit > 0 and transaction.category != "Transfer"
        ]
    elif transaction_type == TransactionType.TRANSFER:
        transactions = [
            transaction
            for transaction in transactions
            if transaction.category == "Transfer"
        ]
    elif transaction_type == TransactionType.ALL:
        transactions = transactions
    else:
        raise ValueError(f"Unknown transaction type {transaction_type}")
    return transactions
