class StopSubscription(Exception):
    def __init__(self, message):
        super().__init__(message)


class RequestProcessingError(Exception):
    def __init__(self, url: str, error_code: int, response: str):
        super().__init__("Failed to process the request '{}'. Error code: '{}'.\nServer response: '{}'".format(
            url, error_code, response))
        self._url = url
        self._error_code = error_code

    @property
    def url(self) -> str:
        return self._url

    @property
    def error_code(self) -> int:
        return self._error_code
