import datetime
import logging
import time
from typing import Dict, List

import requests
import ujson
from prettytable import PrettyTable
from urllib3.exceptions import NewConnectionError

from tinkoff_invest.exceptions import RequestProcessingError
from tinkoff_invest.models.account import Account
from tinkoff_invest.models.candle import Candle
from tinkoff_invest.models.instrument import Instrument
from tinkoff_invest.models.operation import Operation
from tinkoff_invest.models.order import Order
from tinkoff_invest.models.order_book import OrderBook
from tinkoff_invest.models.portfolio import Portfolio, CurrencyPortfolio, PositionPortfolio
from tinkoff_invest.models.types import SubscriptionInterval, OperationType, OperationStatus
from tinkoff_invest.subscriptions import SubscriptionManager

_HTTP_RETRIES_COUNT = 10
_RETRY_TIMEOUT_SEC = 3


class OrderNotification:
    def on_order_completed(self, order: Order, operation: Operation) -> None:
        pass

    def on_order_partially_executed(self, order: Order) -> None:
        pass

    def on_order_status_changed(self, order: Order) -> None:
        pass


class Session(SubscriptionManager):
    def __init__(self, server_address: str, access_token: str, web_socket_server_address: str, account_id: str):
        super().__init__(web_socket_server_address, access_token)
        self._server: str = server_address
        self._auth_headers: Dict[str, str] = {"Authorization": "Bearer " + access_token}
        self._account_id: str = account_id
        self._cached_stocks: Dict[str, Instrument] = {}
        self._cached_currencies: Dict[str, Instrument] = {}
        self._cached_bonds: Dict[str, Instrument] = {}
        self._cached_etfs: Dict[str, Instrument] = {}

    def get_portfolio(self) -> Portfolio:
        positions = self._get('portfolio')
        currencies = self._get('portfolio/currencies')
        return Portfolio(positions, currencies)

    def get_portfolio_currencies(self) -> List[CurrencyPortfolio]:
        currencies = self._get('portfolio/currencies')
        return [CurrencyPortfolio(iterator) for iterator in currencies["payload"]["currencies"]]

    def get_portfolio_positions(self) -> List[PositionPortfolio]:
        positions = self._get('portfolio')
        return [PositionPortfolio(iterator) for iterator in positions["payload"]["positions"]]

    @property
    def stocks(self) -> Dict[str, Instrument]:
        return self._get_instruments(self._cached_stocks, 'market/stocks')

    @property
    def currencies(self) -> Dict[str, Instrument]:
        return self._get_instruments(self._cached_currencies, 'market/currencies')

    @property
    def bonds(self) -> Dict[str, Instrument]:
        return self._get_instruments(self._cached_bonds, 'market/bonds')

    @property
    def etfs(self) -> Dict[str, Instrument]:
        return self._get_instruments(self._cached_etfs, 'market/etfs')

    @property
    def accounts(self) -> List[Account]:
        accounts = self._get('user/accounts')
        return [Account(raw) for raw in accounts["payload"]["accounts"]]

    def get_candles(self, figi: str, start_time: datetime, finish_time: datetime,
                    interval: SubscriptionInterval) -> List[Candle]:
        candles = self._get('market/candles?figi={}&from={}+03:00&to={}+03:00&interval={}'.format(
            figi, start_time.isoformat(), finish_time.isoformat(), interval.value))['payload']['candles']
        return [Candle(iterator) for iterator in candles]

    def get_orderbook(self, figi: str, depth: int) -> OrderBook:
        assert (1 <= depth <= 20), "Depth should be in range [1..20]"
        response = self._get('market/orderbook?figi={}&depth={}'.format(figi, depth))
        return OrderBook(response["payload"])

    def get_instrument_by_ticker(self, ticker: str) -> Instrument:
        instrument = self._get('market/search/by-ticker?ticker={}'.format(ticker))
        assert (instrument["payload"]["total"] == 1), \
            "An unexpected number {} (1 expected) of stocks for ticker '{}'.".format(
                instrument["payload"]["total"], ticker)
        return Instrument(instrument["payload"]["instruments"][0])

    def get_instrument_by_figi(self, figi: str) -> Instrument:
        instrument = self._get('market/search/by-figi?figi={}'.format(figi))
        return Instrument(instrument["payload"])

    def get_orders(self) -> List[Order]:
        return [Order(iterator) for iterator in self._get('orders')['payload']]

    def create_limit_order(self, operation: OperationType, figi: str, price: float, lots: int) -> Order:
        logging.info("Creating limit order %s, figi=%s, price=%f, lots=%d", operation.value, figi, price, lots)
        order = self._post('orders/limit-order?figi={}'.format(figi),
                           {"lots": lots, "operation": operation.value, "price": price})
        return Order(order["payload"])

    def create_market_order(self, operation: OperationType, figi: str, lots: int) -> Order:
        logging.info("Creating market order %s, figi=%s, lots=%d", operation.value, figi, lots)
        order = self._post('orders/market-order?figi={}'.format(figi),
                           {"lots": lots, "operation": operation.value})
        return Order(order["payload"])

    def wait_for_order_completion(self, order: Order, callback_object: OrderNotification) -> None:
        prev_status = order.status
        prev_executed = order.executed_lots
        while True:
            found = False
            for o in self.get_orders():
                if o.id != order.id:
                    continue

                if prev_status != o.status:
                    callback_object.on_order_status_changed(o)
                    prev_status = o.status
                if prev_executed != o.executed_lots:
                    callback_object.on_order_partially_executed(o)
                    prev_executed = o.executed_lots

                time.sleep(1)
                found = True
                break
            if not found:
                today = datetime.datetime.utcnow()
                day_start = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=0, second=0)
                day_end = day_start + datetime.timedelta(days=1)
                operations = self.get_operations(day_start,
                                                 day_end)  # TODO: add order.figi parameter once it will appear API
                for o in operations:
                    if o.id == order.id:
                        if o.status == OperationStatus.DONE and (not o.price or not o.quantity):
                            break  # TODO:remove after https://github.com/TinkoffCreditSystems/invest-openapi/issues/588
                        callback_object.on_order_completed(order, o)
                        return
                time.sleep(1)

    def cancel_order(self, order_id: str) -> None:
        self._post('orders/cancel?orderId={}'.format(order_id), {})

    def get_operations(self, start_time: datetime, finish_time: datetime, figi: str = "") -> List[Operation]:
        request = 'operations?from={}+03:00&to={}+03:00'.format(start_time.isoformat(), finish_time.isoformat())
        if figi:
            request = request + '&figi=' + figi
        return [Operation(op) for op in self._get(request)["payload"]["operations"]]

    def _get(self, query: str) -> dict:
        logging.debug("Making request GET '%s%s'", self._server, query)
        account = "" if not self._account_id else "&brokerAccountId={}".format(self._account_id) if "?" in query \
            else "?brokerAccountId={}".format(self._account_id)
        response = None
        for i in range(1, _HTTP_RETRIES_COUNT):
            try:
                response = requests.get(self._server + query.replace(':', '%3A').replace('+', '%2B') + account,
                                        headers=self._auth_headers)
                if response.status_code != requests.codes.ok:
                    if response.status_code == requests.codes.too_many_requests:
                        time.sleep(_RETRY_TIMEOUT_SEC)
                        return self._get(query)

                    message = response.text
                    if response.status_code not in [requests.codes.service_unavailable, requests.codes.not_found]:
                        dt = ujson.loads(response.text)
                        message = dt["payload"]["message"]
                    logging.error("Request failed:\nURL: %s\nStatus: %d\nResponse: %s", response.url,
                                  response.status_code, message)
                    raise RequestProcessingError(response.url, response.status_code, response.text)
                logging.debug("Response is '%s'", response.text)
                return ujson.loads(response.text)
            except ConnectionError as err:
                logging.error("Unable to process '{}' request due to connection error: {}".format(query, err))
                time.sleep(_RETRY_TIMEOUT_SEC)
            except NewConnectionError as err:
                logging.error("Unable to process '{}' request due to connection error: {}".format(query, err))
                time.sleep(_RETRY_TIMEOUT_SEC)
            except ValueError as err:
                logging.error("Unable to process '{}' request. An invalid result from server: '{}', error: {}".format(
                    query, response.text if response else "", err))
        raise RequestProcessingError(response.url, response.status_code, response.text)

    def _post(self, query: str, data: dict) -> dict:
        logging.debug("Making request POST '%s%s' with body '%s'", self._server, query, data)
        response = requests.post(self._server + query, headers=self._auth_headers, data=ujson.dumps(data))
        if response.status_code != requests.codes.ok:
            message = response.text
            if response.status_code not in [requests.codes.service_unavailable, requests.codes.unauthorized]:
                message = ujson.loads(response.text)["payload"]["message"]
            logging.error("Request failed:\nURL: %s\nBody %s\nStatus: %d\nResponse: %s", response.url,
                          str(data), response.status_code, message)
            raise RequestProcessingError(response.url, response.status_code, response.text)
        logging.debug("Response is '%s'", response.text)
        return ujson.loads(response.text)

    def _get_instruments(self, cache: Dict[str, Instrument], url: str) -> Dict[str, Instrument]:
        if cache:
            return cache
        instruments = self._get(url)
        cache = {}
        for raw in instruments["payload"]["instruments"]:
            inst = Instrument(raw)
            cache[inst.ticker] = inst
        return cache

    def __str__(self) -> str:
        result = "Accounts:\n{}"
        table = PrettyTable(field_names=['ID', 'Type'])
        for acc in self.accounts:
            table.add_row([acc.id, acc.type.name])
        return result.format(table)
