import json
import enum

import streamlit as st
import pandas as pd


class Currency(enum.Enum):
    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"


class Account:
    def __init__(
        self,
        name: str,
        iban: str,
        currency: Currency,
        starting_balance: float = 0.0,
        balance: float = 0.0,
        bank: str = "",
        account_number: str = "",
    ):
        self.name = name
        self.iban = iban
        self.currency = currency
        self.starting_balance = starting_balance
        self.balance = balance
        self.bank = bank
        self.account_number = account_number

    def already_exists(self, accounts: dict) -> bool:
        for existing_account in accounts.values():
            if (
                self.name == existing_account["name"]
                or self.iban == existing_account["iban"]
            ):
                return True
        return False

    def is_valid(self) -> bool:
        return self.name and self.iban

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "bank": self.bank,
            "account_number": self.account_number,
            "iban": self.iban,
            "currency": self.currency.value,
            "starting_balance": self.starting_balance,
            "balance": self.balance,
        }

    @staticmethod
    def from_dict(account_dict: dict) -> "Account":
        return Account(
            name=account_dict["name"],
            iban=account_dict["iban"],
            currency=Currency(account_dict["currency"]),
            starting_balance=account_dict["starting_balance"],
            balance=account_dict["balance"],
            bank=account_dict["bank"],
            account_number=account_dict["account_number"],
        )
