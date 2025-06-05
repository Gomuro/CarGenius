from abc import ABC, abstractmethod
from ..proxy import ProxyABC, EmptyProxy

class BaseAlgorithm(ABC):
    def __init__(self, executable_path: str,
                 proxy: ProxyABC = EmptyProxy(),
                 user_agent: str = '',
                 headless=True,
                 window_size=(400, 700),
                 logger=None):
        self.executable_path = executable_path
        self.proxy = proxy
        self.user_agent = user_agent
        self.headless = headless
        self.window_size = window_size
        self.logger = logger
        self.driver = None
        self._running = True

    @abstractmethod
    def run(self):
        """This method should be implemented by subclasses."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the algorithm execution"""
        pass

    def handle_exception(self, message: str, exception: Exception):
        """Handle exceptions with logging."""
        if self.logger:
            self.logger.error(message, exc_info=True)

    # __del__ removed 