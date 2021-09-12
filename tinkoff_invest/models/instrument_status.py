from typing import Optional

from prettytable import PrettyTable

from tinkoff_invest.models.types import TradingStatus


class InstrumentStatus:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def trading_status(self) -> TradingStatus:
        return TradingStatus(self._data["trade_status"])

    @property
    def min_price_increment(self) -> float:
        return float(self._data["min_price_increment"])

    @property
    def lot_size(self) -> int:
        return int(self._data["lot"])

    @property
    def accrued_interest(self) -> Optional[float]:
        return self._data.get("accrued_interest", None)

    @property
    def limit_up(self) -> Optional[float]:
        return self._data.get("limit_up", None)

    @property
    def limit_down(self) -> Optional[float]:
        return self._data.get("limit_down", None)

    @property
    def figi(self) -> str:
        return self._data["figi"]

    def __str__(self) -> str:
        table = PrettyTable(field_names=['FIGI', 'Status', 'Min price increment', 'Lot size', 'Limit Up', 'Limit Down'])
        table.add_row([self.figi, self.trading_status.name, self.min_price_increment, self.lot_size, self.limit_up,
                       self.limit_down])
        return str(table)
