from enum import Enum


class Currency(Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


CURRENCIES_SIGNS = {
    Currency.RUB: '₽',
    Currency.USD: '$',
    Currency.EUR: '€'
}


class OperationType(Enum):
    BUY = "Buy"
    BUY_CARD = "BuyCard"
    BROKER_COMMISSION = "BrokerCommission"
    COUPON = "Coupon"
    DIVIDEND = "Dividend"
    EXCHANGE_COMMISSION = "ExchangeCommission"
    SERVICE_COMMISSION = "ServiceCommission"
    MARGIN_COMMISSION = "MarginCommission"
    PART_REPAYMENT = "PartRepayment"
    PAY_IN = "PayIn"
    PAY_OUT = "PayOut"
    REPAYMENT = "Repayment"
    SECURITY_IN = "SecurityIn"
    SECURITY_OUT = "SecurityOut"
    SELL = "Sell"
    TAX = "Tax"
    TAX_BACK = "TaxBack"
    TAX_DIVIDEND = "TaxDividend"
    TAX_LUCRE = "TaxLucre"
    TAX_COUPON = "TaxCoupon"


class SubscriptionInterval(Enum):
    MINUTES_1 = "1min"
    MINUTES_2 = "2min"
    MINUTES_3 = "3min"
    MINUTES_5 = "5min"
    MINUTES_10 = "10min"
    MINUTES_15 = "15min"
    MINUTES_30 = "30min"
    HOUR_1 = "hour"
    HOUR_2 = "2hour"
    HOUR_4 = "4hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class OrderStatus(Enum):
    NEW = "New"
    PARTIALLY_FILL = "PartiallyFill"
    FILL = "Fill"
    CANCELLED = "Cancelled"
    REPLACED = "Replaced"
    PENDING_CANCEL = "PendingCancel"
    REJECTED = "Rejected"
    PENDING_REPLACE = "PendingReplace"
    PENDING_NEW = "PendingNew"


class OrderType(Enum):
    LIMIT = "Limit"
    MARKET = "Market"


class OperationStatus(Enum):
    DONE = "Done"
    DECLINE = "Decline"
    PROGRESS = "Progress"


class InstrumentType(Enum):
    STOCK = "Stock"
    CURRENCY = "Currency"
    BOND = "Bond"
    ETF = "Etf"


class TradingStatus(Enum):
    TRADING_NOT_AVAILABLE = "not_available_for_trading"
    OPENING_AUCTION = "opening_auction"
    NORMAL_TRADING = "normal_trading"
    BREAK = "break_in_trading"
    CLOSING_PRICE_TRADING = "trading_at_closing_auction_price"
    CLOSING_AUCTION = "closing_auction"
    CLOSING_PERIOD = "closing_period"
    OPENING_PERIOD = "opening_period"
    TRADING_NOT_AVAILABLE_REST = "NotAvailableForTrading"
    NORMAL_TRADING_REST = "NormalTrading"


class AccountType(Enum):
    TINKOFF = "Tinkoff"
    TINKOFF_IIS = "TinkoffIis"


class SubscriptionEventType(Enum):
    CANDLE = "candle"
    ORDER_BOOK = "orderbook"
    INSTRUMENT = "instrument_info"
