import gc
import logging
import threading
import ujson
import websocket
import time
import random
from typing import List, Optional, Dict, Union
from queue import Queue

from tinkoff_invest.config import EVENTS_PROCESSING_WORKERS_COUNT
from tinkoff_invest.base_strategy import BaseStrategy
from tinkoff_invest.models.candle import Candle
from tinkoff_invest.models.instrument_status import InstrumentStatus
from tinkoff_invest.models.types import SubscriptionInterval, SubscriptionEventType
from tinkoff_invest.models.order_book import OrderBook

_SUBSCRIPTION_RETRIES_COUNT = 15
_SUBSCRIPTION_TIMEOUT_SEC = 60


def _build_subscription_name(figi: str, obj_type: str, param: str) -> str:
    return "{}_{}_{}".format(figi, obj_type, param)


def _parse_subscription_name(name: str) -> (str, str, str):
    return name.split('_')


class SubscriptionManager:
    MAX_RECONNECT_ATTEMPTS = 5

    def __init__(self, server: str, token: str):
        self._ws_server: str = server
        self._token: str = token

        self._subscriptions: Dict[str, List[Dict[str, Union[Dict, BaseStrategy]]]] = {}
        self._web_socket: Optional[websocket.WebSocketApp] = None
        self._workers: List[threading.Thread] = []
        self._queue: Queue = Queue()
        self._connection_established: bool = False
        self._stop_flag: bool = False
        self._shall_reconnect: bool = False
        self._reconnect_retries: int = 0

    def __del__(self):
        self._deinitialize_workers()
        if self._connection_established:
            self._web_socket.close()
            self._connection_established = False

    def _initialize_workers(self) -> None:
        for i in range(EVENTS_PROCESSING_WORKERS_COUNT):
            thread = threading.Thread(target=self._worker, daemon=True)
            thread.start()
            self._workers.append(thread)
        logging.info("%d workers are ready to process events", EVENTS_PROCESSING_WORKERS_COUNT)

    def _deinitialize_workers(self) -> None:
        if not self._workers:
            return

        logging.info("Shutdown subscription workers")
        self._stop_flag = True
        for worker in self._workers:
            try:
                if worker.is_alive():
                    worker.join(1)
            except Exception as err:
                logging.error("Unable to join tread, {}".format(err))
        self._workers: List[threading.Thread] = []

    def _ws_connect(self) -> None:
        while True:
            self._web_socket = websocket.WebSocketApp(self._ws_server, ["Authorization: Bearer " + self._token],
                                                      on_message=self._on_subscription_event, on_error=self._on_error,
                                                      on_close=self._on_close, on_open=self._on_open)
            logging.info("Starting WebSocketApp connection")
            self._web_socket.run_forever()

            while self._shall_reconnect and self._reconnect_retries < self.MAX_RECONNECT_ATTEMPTS:
                gc.collect()
                logging.info("Connection lost, trying to reconnect...")
                # sleep between reties should increase such as truncated binary exponential backoff with 32 seconds limit
                sleep_time = 2 ** self._reconnect_retries + random.uniform(0, 1) if self._reconnect_retries < 6 else 32
                logging.info(f"...sleeping {sleep_time:.2f} seconds before retry...")
                time.sleep(sleep_time)
                self._reconnect_retries += 1
                self._web_socket.keep_running = True
                self._web_socket.run_forever()

            self._shall_reconnect = False
            if self._web_socket:
                self._web_socket.close()
                self._web_socket = None

    def _initialize_web_sockets(self) -> None:
        self._ws_thread: threading.Thread = threading.Thread(target=self._ws_connect, daemon=True)
        self._ws_thread.start()
        while True:
            if self._connection_established:
                break
            time.sleep(0.01)
        logging.info("Web socket client started")

    def _on_open(self, _) -> None:
        self._connection_established = True
        self._reconnect_retries = 0
        logging.info("Web socket connection opened")
        if self._shall_reconnect:
            self._restart_workers_and_resubscribe()

    def _on_error(self, _, error: Exception) -> None:
        logging.exception(error)
        self._deinitialize_workers()
        self._connection_established = False
        self._shall_reconnect = True

    def _on_close(self, _1, _2, _3) -> None:
        logging.warning("Web socket has been closed")
        self._deinitialize_workers()
        self._connection_established = False

    def _worker(self) -> None:
        while True:
            try:
                if self._stop_flag:
                    logging.info("Shutdown worker")
                    break

                if self._queue.qsize() > EVENTS_PROCESSING_WORKERS_COUNT - 1:
                    logging.warning("Too many events to process: {}".format(self._queue.qsize()))

                event = self._queue.get()
                obj = ujson.loads(event)
                if obj["event"] == SubscriptionEventType.CANDLE.value:
                    candle = Candle(obj["payload"])
                    name = _build_subscription_name(obj["payload"]["figi"], obj["event"], obj["payload"]["interval"])
                    for subscription in self._subscriptions[name]:
                        subscription['strategy'].on_candle(candle)
                elif obj["event"] == SubscriptionEventType.ORDER_BOOK.value:
                    order_book = OrderBook(obj["payload"])
                    name = _build_subscription_name(obj["payload"]["figi"], obj["event"], obj["payload"]["depth"])
                    for subscription in self._subscriptions[name]:
                        subscription['strategy'].on_order_book(order_book)
                elif obj["event"] == SubscriptionEventType.INSTRUMENT.value:
                    info = InstrumentStatus(obj["payload"])
                    name = _build_subscription_name(obj["payload"]["figi"], obj["event"], "")
                    for subscription in self._subscriptions[name]:
                        subscription['strategy'].on_instrument_info(info)
                else:
                    raise Exception("An unsupported event type '{}'".format(obj["event"]))
                logging.debug("Event has been processed: %s", event)
                self._queue.task_done()
            except Exception as err:
                self._on_error(self._ws_server, err)

    def _on_subscription_event(self, _, event: str) -> None:
        logging.debug("New event: %s", event)
        if not self._stop_flag:
            self._queue.put(event)

    def _subscribe(self, argument: dict, subscription_name: str, strategy: BaseStrategy) -> None:
        if not self._web_socket:
            self._initialize_web_sockets()
            self._initialize_workers()

        self._web_socket.send(ujson.dumps(argument))
        if subscription_name not in self._subscriptions:
            self._subscriptions[subscription_name] = [{'argument': argument,
                                                      'strategy': strategy}]
        else:
            self._subscriptions[subscription_name].append({'argument': argument,
                                                           'strategy': strategy})

    def _restart_workers_and_resubscribe(self):
        self._shall_reconnect = False
        self._stop_flag = False
        self._initialize_workers()

        for subscription_name, strategies in self._subscriptions.items():
            logging.info(f"Resubscribing to subscription: {subscription_name}")
            for strategy_details in strategies:
                logging.info(f"...using strategy {strategy_details['strategy']} with {strategy_details['argument']}")
                self._web_socket.send(ujson.dumps(strategy_details['argument']))

    def _unsubscribe(self, argument: dict, subscription_name: str) -> None:
        self._web_socket.send(ujson.dumps(argument))
        if len(self._subscriptions[subscription_name]) == 1:
            del self._subscriptions[subscription_name]
        else:
            pass  # TODO: how to remove specific strategy

    def subscribe_to_candles(self, figi: str, interval: SubscriptionInterval, strategy: BaseStrategy) -> None:
        subscription_name = _build_subscription_name(figi, "candle", interval.value)
        self._subscribe({"event": "candle:subscribe", "figi": figi, "interval": interval.value},
                        subscription_name, strategy)
        logging.info("Candle subscription created (%s, %s)", figi, interval.value)

    def unsubscribe_from_candles(self, figi: str, interval: SubscriptionInterval) -> None:
        subscription_name = _build_subscription_name(figi, "candle", interval.value)
        self._unsubscribe({"event": "candle:unsubscribe", "figi": figi, "interval": interval.value}, subscription_name)
        logging.info("Candle subscription removed (%s, %s)", figi, interval.value)

    def subscribe_to_order_book(self, figi: str, depth: int, strategy: BaseStrategy) -> None:
        assert (0 < depth <= 20), "Depth should be > 0 and <= 20"
        subscription_name = _build_subscription_name(figi, "orderbook", str(depth))
        self._subscribe({"event": "orderbook:subscribe", "figi": figi, "depth": depth}, subscription_name, strategy)
        logging.info("OrderBook subscription created (%s, %s)", figi, str(depth))

    def unsubscribe_from_order_book(self, figi: str, depth: int) -> None:
        subscription_name = _build_subscription_name(figi, "orderbook", str(depth))
        self._unsubscribe({"event": "orderbook:unsubscribe", "figi": figi, "depth": depth}, subscription_name)
        logging.info("OrderBook subscription removed (%s, %s)", figi, str(depth))

    def subscribe_to_instrument_info(self, figi: str, strategy: BaseStrategy) -> None:
        subscription_name = _build_subscription_name(figi, "instrument_info", "")
        self._subscribe({"event": "instrument_info:subscribe", "figi": figi}, subscription_name, strategy)
        logging.info("InstrumentInfo subscription created (%s)", figi)

    def unsubscribe_from_instrument_info(self, figi: str) -> None:
        subscription_name = _build_subscription_name(figi, "instrument_info", "")
        self._unsubscribe({"event": "instrument_info:unsubscribe", "figi": figi}, subscription_name)
        logging.info("InstrumentInfo subscription removed (%s)", figi)
