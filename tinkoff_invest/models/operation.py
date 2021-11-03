import datetime
from typing import Optional
from iso8601 import iso8601

from prettytable import PrettyTable

from tinkoff_invest.models.money import MoneyAmount, build_money_amount
from tinkoff_invest.models.types import OperationType, OperationStatus, Currency, InstrumentType


class Operation:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def figi(self) -> str:
        return self._data.get("figi", "")

    @property
    def operation(self) -> OperationType:
        return OperationType(self._data["operationType"])

    @property
    def status(self) -> OperationStatus:
        return OperationStatus(self._data["status"])

    @property
    def instrument_type(self) -> Optional[InstrumentType]:
        return InstrumentType(self._data["instrumentType"]) if "instrumentType" in self._data else None

    @property
    def currency(self) -> Currency:
        return Currency(self._data["currency"])

    @property
    def payment(self) -> MoneyAmount:
        return build_money_amount(abs(float(self._data["payment"])), Currency(self._data["currency"]))

    @property
    def price(self) -> MoneyAmount:
        return build_money_amount(float(self._data["price"]) if "price" in self._data else 0.0,
                                  Currency(self._data["currency"]))

    @property
    def quantity(self) -> Optional[int]:
        return int(self._data["quantityExecuted"]) if "quantityExecuted" in self._data else None

    @property
    def date(self) -> datetime.date:
        return iso8601.parse_date(self._data["date"])

    @property
    def is_margin(self) -> Optional[bool]:
        return bool(self._data["isMarginCall"]) if "isMarginCall" in self._data else None

    @property
    def commission(self) -> MoneyAmount:
        if "commission" not in self._data:
            return MoneyAmount()
        return MoneyAmount(self._data["commission"])

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Date', 'Operation', 'Instrument', 'Figi', 'Payment', 'Price', 'Commission'])
        table.add_row([str(self.date), self.operation.name, self.instrument_type.name if self.instrument_type else "",
                       self.figi, self.payment, self.price if self.price else "", self.commission])
        return str(table)
