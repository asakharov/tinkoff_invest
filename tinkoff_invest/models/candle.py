import datetime
import iso8601

from prettytable import PrettyTable

from tinkoff_invest.models.types import SubscriptionInterval


class Candle:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def open_price(self) -> float:
        return float(self._data["o"])

    @property
    def close_price(self) -> float:
        return float(self._data["c"])

    @property
    def highest_price(self) -> float:
        return float(self._data["h"])

    @property
    def lowest_price(self) -> float:
        return float(self._data["l"])

    @property
    def volume(self) -> float:
        return float(self._data["v"])

    @property
    def time(self) -> datetime.date:
        return iso8601.parse_date(self._data["time"])

    @property
    def interval(self) -> SubscriptionInterval:
        return SubscriptionInterval(self._data["interval"])

    @property
    def figi(self) -> str:
        return self._data["figi"]

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Time', 'Interval', 'FIGI', 'Open', 'Close', 'High', 'Low', 'Volume'])
        table.add_row([self.time, self.interval.name, self.figi, self.open_price, self.close_price, self.highest_price,
                       self.lowest_price, self.volume])
        return str(table)
