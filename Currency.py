import enum


class Currency(enum.StrEnum):
    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"


class CurrencyConverter:
    # TODO:
    # - Get the real rates
    # - Get the rates from a service
    RATES = {
        Currency.CHF: {
            Currency.CHF: 1.0,
            Currency.EUR: 0.92,
            Currency.USD: 1.08,
        },
        Currency.EUR: {
            Currency.CHF: 1.08,
            Currency.EUR: 1.0,
            Currency.USD: 1.18,
        },
        Currency.USD: {
            Currency.CHF: 0.92,
            Currency.EUR: 0.85,
            Currency.USD: 1.0,
        },
    }

    @classmethod
    def convert(
        cls, amount: float, from_currency: Currency, to_currency: Currency
    ) -> float:
        return amount * cls.RATES[from_currency][to_currency]
