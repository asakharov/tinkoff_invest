import logging
from typing import List, Optional

from prettytable import PrettyTable

from tinkoff_invest.models.money import MoneyAmount, build_money_amount
from tinkoff_invest.models.types import InstrumentType, Currency


class CurrencyPortfolio:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def name(self) -> Currency:
        return Currency(self._data["currency"])

    @property
    def balance(self) -> MoneyAmount:
        return build_money_amount(float(self._data["balance"]), Currency(self._data["currency"]))

    @property
    def blocked(self) -> float:
        return float(self._data.get("blocked", 0.0))

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Name', 'Balance', 'Blocked'])
        table.add_row([self.name.name, self.balance, self.blocked])
        return str(table)


class PositionPortfolio:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def figi(self) -> str:
        return self._data["figi"]

    @property
    def ticker(self) -> str:
        return self._data["ticker"]

    @property
    def isin(self) -> str:
        return self._data["isin"]

    @property
    def type(self) -> InstrumentType:
        return InstrumentType(self._data["instrumentType"])

    @property
    def balance(self) -> float:
        return float(self._data["balance"])

    @property
    def lots(self) -> int:
        return self._data["lots"]

    @property
    def blocked(self) -> float:
        return float(self._data["blocked"])

    @property
    def expected_yield(self) -> MoneyAmount:
        return MoneyAmount(self._data["expectedYield"] if "expectedYield" in self._data else None)

    @property
    def average_price(self) -> MoneyAmount:
        return MoneyAmount(self._data["averagePositionPrice"] if "averagePositionPrice" in self._data else None)

    @property
    def average_price_no_nkd(self) -> MoneyAmount:
        return MoneyAmount(self._data["averagePositionPriceNoNkd"]
                           if "averagePositionPriceNoNkd" in self._data else None)

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Ticker', 'Name', 'Type', 'Balance', 'Lots', 'Avg price'])
        table.add_row([self.ticker, self.name, self.type.value, int(self.balance), self.lots, self.average_price])
        return str(table)


class Portfolio:
    def __init__(self, positions: dict, currencies: dict):
        self._positions = [PositionPortfolio(raw) for raw in positions["payload"]["positions"]]
        self._positions = list(filter(lambda pos: pos.type != 'Currency', self._positions))
        self._positions: List[PositionPortfolio] = sorted(self._positions, key=lambda item: item.type.value)
        self._currencies: List[CurrencyPortfolio] =\
            [CurrencyPortfolio(raw) for raw in currencies["payload"]["currencies"]]

    @property
    def positions(self) -> List[PositionPortfolio]:
        return self._positions

    @property
    def currencies(self) -> List[CurrencyPortfolio]:
        return self._currencies

    def get_position_by_figi(self, figi: str) -> Optional[PositionPortfolio]:
        for position in self.positions:
            if position.figi == figi:
                return position
        logging.warning("Position with figi == %s not found", figi)
        return None

    def get_position_by_ticker(self, ticker: str) -> Optional[PositionPortfolio]:
        for position in self.positions:
            if position.ticker == ticker:
                return position
        logging.warning("Position with ticker == %s not found", ticker)
        return None

    def __str__(self) -> str:
        table = PrettyTable(field_names=['Currency', 'Type', 'Sum'])
        for item in self._currencies:
            table.add_row([item.name.value, "Currency", item.balance])

        result = str(table)
        result += "\n"
        table_pos = PrettyTable(field_names=['Ticker', 'Name', 'Type', 'Balance', 'Lots', 'Avg. price'])
        for item in self.positions:
            if item.type == InstrumentType.CURRENCY:
                continue
            table_pos.add_row([item.ticker, item.name, item.type.value, item.balance, item.lots, item.average_price])
        result += str(table_pos)
        return result
