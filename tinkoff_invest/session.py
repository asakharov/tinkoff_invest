from tinkoff_invest.config import SANDBOX_SERVER, PRODUCTION_SERVER, WEB_SOCKETS_SERVER
from tinkoff_invest.base_session import Session
from tinkoff_invest.models.types import Currency


class ProductionSession(Session):
    def __init__(self, token: str, server_address: str = PRODUCTION_SERVER,
                 web_socket_server_address: str = WEB_SOCKETS_SERVER, account_id: str = ""):
        super().__init__(server_address, token, web_socket_server_address, account_id)


class SandboxSession(Session):
    def __init__(self, token: str, server_address: str = SANDBOX_SERVER,
                 web_socket_server_address: str = WEB_SOCKETS_SERVER, account_id: str = ""):
        super().__init__(server_address, token, web_socket_server_address, account_id)
        self._register()

    def _register(self) -> None:
        auth_result = self._post('sandbox/register', {"brokerAccountType": "Tinkoff"})
        assert(auth_result["status"].lower() == "ok"), "Token registration failed"

    def set_currency_balance(self, currency: Currency, balance: float) -> None:
        self._post('sandbox/currencies/balance', {"currency": currency.value, "balance": balance})

    def set_position_balance(self, pos_id: str, balance: int) -> None:
        self._post('sandbox/positions/balance', {"figi": pos_id, "balance": balance})

    def remove(self) -> None:
        self._post('sandbox/remove', {})

    def clear_all_positions(self) -> None:
        self._post('sandbox/clear', {})
