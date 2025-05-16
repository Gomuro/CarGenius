from PyQt6.QtWidgets import QWidget

class BaseComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()
        self._connect_signals()

    def _create_ui(self):
        """Must be implemented by subclasses"""
        raise NotImplementedError

    def _connect_signals(self):
        """Optional signal connections"""
        pass 