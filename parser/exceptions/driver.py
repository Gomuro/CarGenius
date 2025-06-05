class DriverError(Exception):
    pass


class DriverWarning(Exception):
    pass


class TryAgainPageError(DriverError):
    pass


class BrowserClosedError(DriverError):
    pass


class AccessDeniedError(Exception):
    """Raised when access denied page is detected"""


class NoProxyProvidedError(Exception):
    """Raised when no proxy is provided and direct connection is used"""
