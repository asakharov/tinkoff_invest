from prettytable import PrettyTable

from tinkoff_invest.models.types import AccountType


class Account:
    def __init__(self, raw_data: dict):
        self._data = raw_data

    @property
    def type(self) -> AccountType:
        return AccountType(self._data["brokerAccountType"])

    @property
    def id(self) -> str:
        return self._data["brokerAccountId"]

    def __str__(self) -> str:
        table = PrettyTable(field_names=['ID', 'Type'])
        table.add_row([self.id, self.type.name])
        return str(table)
