from typing import Optional

from tinkoff_invest.models.types import Currency, CURRENCIES_SIGNS


class MoneyAmount:
    def __init__(self, raw_data: Optional[dict] = None):
        self._data = raw_data

    @property
    def currency(self) -> Currency:
        return Currency(self._data["currency"]) if self._data else Currency.RUB

    @property
    def value(self) -> float:
        return abs(float(self._data["value"])) if self._data else 0.0

    def __add__(self, other):
        if not self._data:
            self._data = {"currency": other.currency, "value": other.value}
        else:
            assert(self._data["currency"] == self._data["currency"]), "Currencies should be the same"
            self._data["value"] += other.value
        return self

    def __sub__(self, other):
        assert self._data, "Decreasing number should not be empty"
        assert(self._data["currency"] == self._data["currency"]), "Currencies should be the same"
        self._data["value"] -= other.value
        return self

    def __str__(self) -> str:
        return "{} {}".format(self.value, CURRENCIES_SIGNS[self.currency])


def build_money_amount(value: float, currency: Currency) -> MoneyAmount:
    return MoneyAmount({"value": value, "currency": currency})
