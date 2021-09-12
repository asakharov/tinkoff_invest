from typing import Optional

from prettytable import PrettyTable

from tinkoff_invest.models.money import MoneyAmount
from tinkoff_invest.models.types import OrderType, OperationType, OrderStatus


class Order:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def id(self) -> str:
        return self._data["orderId"]

    @property
    def figi(self) -> str:
        return self._data['figi']

    @property
    def type(self) -> OrderType:
        return OrderType(self._data['type'])

    @property
    def operation(self) -> OperationType:
        return OperationType(self._data["operation"])

    @property
    def status(self) -> OrderStatus:
        return OrderStatus(self._data["status"])

    @property
    def reject_reason(self) -> str:
        return self._data["rejectReason"] if "rejectReason" in self._data else ""

    @property
    def requested_lots(self) -> int:
        return self._data["requestedLots"]

    @property
    def executed_lots(self) -> int:
        return self._data["executedLots"]

    @property
    def price(self) -> Optional[float]:
        if 'price' in self._data:
            return float(self._data['price'])
        else:
            return None

    @property
    def commission(self) -> MoneyAmount:
        if "commission" not in self._data:
            return MoneyAmount()
        return MoneyAmount(self._data["commission"])

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Operation', 'Status', 'Requested Lots', 'Executed Lots',
                                         'Commission', 'Reason'])
        table.add_row([self.operation.name, self.status.name, self.requested_lots, self.executed_lots,
                       "{} {}".format(self.commission.value, self.commission.currency.name), self.reject_reason])
        return str(table)
