from typing import List

from prettytable import PrettyTable

from tinkoff_invest.models.types import TradingStatus


class OrderBook:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def bids(self) -> List[List[float]]:
        return self._data["bids"]

    @property
    def asks(self) -> List[List[float]]:
        return self._data["asks"]

    @property
    def depth(self) -> int:
        return self._data["depth"]

    @property
    def figi(self) -> str:
        return self._data["figi"]

    @property
    def trading_status(self) -> TradingStatus:
        return TradingStatus(self._data["tradeStatus"])

    @property
    def face_value(self) -> float:
        return self._data["faceValue"]

    @property
    def last_price(self) -> float:
        return self._data["lastPrice"]

    @property
    def close_price(self) -> float:
        return self._data["closePrice"]

    @property
    def limit_up(self) -> float:
        return self._data["limitUp"] if "limitUp" in self._data else 0.0

    @property
    def limit_down(self) -> float:
        return self._data["limitDown"] if "limitDown" in self._data else 0.0

    def __str__(self) -> str:
        table = PrettyTable(field_names=['FIGI', 'Asks', 'Bids', 'Last price', 'Close price'])
        table.add_row([self.figi, self.asks, self.bids, self.last_price, self.close_price])
        return str(table)
