from prettytable import PrettyTable

from tinkoff_invest.models.money import build_money_amount, MoneyAmount
from tinkoff_invest.models.types import Currency, InstrumentType


class Instrument:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def figi(self) -> str:
        return self._data["figi"]

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def type(self) -> InstrumentType:
        return InstrumentType(self._data["type"])

    @property
    def ticker(self) -> str:
        return self._data["ticker"]

    @property
    def isin(self) -> str:
        return self._data["isin"]

    @property
    def currency(self) -> Currency:
        return Currency(self._data["currency"])

    @property
    def min_price_increment(self) -> MoneyAmount:
        return build_money_amount(float(self._data["minPriceIncrement"]), Currency(self._data["currency"]))

    @property
    def lot_size(self) -> int:
        return int(self._data["lot"])

    @property
    def min_quantity(self) -> int:
        return int(self._data["minQuantity"])

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Ticker', 'Name', 'Type', 'Min price increment', 'Lot size', 'Currency'])
        table.add_row([self.ticker, self.name, self.type.value, self.min_price_increment, self.lot_size,
                       self.currency.value])
        return str(table)
