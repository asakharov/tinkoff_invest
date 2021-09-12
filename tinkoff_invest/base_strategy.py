from tinkoff_invest.models.candle import Candle
from tinkoff_invest.models.instrument_status import InstrumentStatus
from tinkoff_invest.models.order_book import OrderBook


class BaseStrategy:
    def on_candle(self, candle: Candle) -> None:
        pass

    def on_order_book(self, order_book: OrderBook) -> None:
        pass

    def on_instrument_info(self, instrument: InstrumentStatus) -> None:
        pass
