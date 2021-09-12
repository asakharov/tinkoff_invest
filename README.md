# tinkoff_invest

### Установка

Вы можете установить Tinkoff invest клиент используя [PyPI](https://pypi.org/project/tinkoff_invest/):

    pip install tinkoff_invest

Для работы данного клиента необходим Python 3.8+.

### Где взять токен аутентификации?


* Авторизируйтесь в [личном кабинете](https://www.tinkoff.ru/summary/) Тинькофф.
* Перейдите в раздел [настройки](https://www.tinkoff.ru/invest/settings/) Инвестиций.
* Убедитесь, что функция "Подтверждение сделок кодом" отключена.
* В подразделе "Токен для OpenAPI" выпустите нужный вам токен - для торговли и\или для песочницы.

### Примеры использования

Распечатка портфолио:
```python
from tinkoff_invest import ProductionSession


def _dump_portfolio(session):
    print("My Portolio")
    for pos in session.get_portfolio().positions:
        print(pos)

    for cur in session.get_portfolio().currencies:
        print(cur)


if __name__ == "__main__":
    prod_session = ProductionSession('%MY_TOKEN%')
    _dump_portfolio(prod_session)
```

Подписка на изменение цен\свойств биржевого инструмента:
```python
import time

from tinkoff_invest import ProductionSession
from tinkoff_invest.base_strategy import BaseStrategy
from tinkoff_invest.models.candle import Candle
from tinkoff_invest.models.instrument_status import InstrumentStatus
from tinkoff_invest.models.order_book import OrderBook
from tinkoff_invest.models.types import SubscriptionInterval


class TestStrategy(BaseStrategy):
    def __init__(self):
        self.counter = 0

    def on_candle(self, candle: Candle) -> None:
        print(candle)

    def on_order_book(self, order_book: OrderBook) -> None:
        pass

    def on_instrument_info(self, instrument: InstrumentStatus) -> None:
        pass


if __name__ == "__main__":
    prod_session = ProductionSession('%MY_TOKEN%')
    strategy = TestStrategy()
    prod_session.subscribe_to_candles(prod_session.get_instrument_by_ticker("SBER").figi,
                                      SubscriptionInterval.HOUR_1, strategy)
    while True:
        time.sleep(1)
```