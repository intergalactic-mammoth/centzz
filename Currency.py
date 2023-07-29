import enum
import functools

from forex_python.converter import CurrencyRates


class Currency(enum.StrEnum):
    """A currency."""

    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"


class CurrencyConverter:
    """A currency converter."""

    c = CurrencyRates()

    # Cache the rates to avoid unnecessary API calls.
    @classmethod
    @functools.cache
    def get_rate(cls, from_currency: Currency, to_currency: Currency) -> float:
        """Returns the rate from the given currency to the given currency."""
        return cls.c.get_rate(from_currency, to_currency)

    @classmethod
    def convert(
        cls, amount: float, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Converts the given amount from the given currency to the given currency."""
        return amount * cls.get_rate(from_currency, to_currency)
