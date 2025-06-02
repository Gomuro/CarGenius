class DriverError(Exception):
    pass


class DriverWarning(Exception):
    pass


class TryAgainPageError(DriverError):
    pass


class BrowserClosedError(DriverError):
    pass
